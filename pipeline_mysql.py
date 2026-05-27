"""
=============================================================================
 Pipeline RFM — Segmentation clients e-commerce UK
 Algo & BDD - INSEEC MSc2 Manager Data Marketing 2026
=============================================================================
 Charge données MySQL → Calcul RFM → Enrichissement API ExchangeRate → 
 Écriture résultats dans table rfm_results
=============================================================================
"""

from dotenv import load_dotenv
load_dotenv()

import os
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import mysql.connector

# Configuration MySQL
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "ecommerce_rfm"),
    "port": int(os.getenv("DB_PORT", "3306")),
}

def get_exchange_rate():
    """Récupère le taux de change GBP → EUR depuis API externe"""
    try:
        resp = requests.get("https://api.exchangerate-api.com/v4/latest/GBP", timeout=5)
        rate = resp.json()["rates"]["EUR"]
        print(f"✓ Taux GBP→EUR : {rate:.4f}")
        return rate
    except Exception as e:
        print(f"⚠ Erreur API, utilisation taux par défaut : {e}")
        return 1.16

def load_orders_data():
    """Charge les données depuis MySQL"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    query = """
    SELECT o.invoice_no, o.customer_id, o.invoice_date, 
           oi.quantity, oi.unit_price, oi.line_total 
    FROM orders o 
    INNER JOIN order_items oi ON o.invoice_no = oi.invoice_no 
    INNER JOIN customers c ON o.customer_id = c.customer_id 
    WHERE o.customer_id IS NOT NULL
    """
    
    cursor.execute(query)
    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    df = pd.DataFrame(data, columns=columns)
    print(f"✓ {len(df)} lignes chargées depuis MySQL")
    return df

def clean_data(df):
    """Nettoie les données (supprime les NULL)"""
    return df.dropna()

def compute_rfm(df, exchange_rate=1.16):
    """
    Calcule les scores RFM pour chaque client
    - R (Recency) : jours depuis dernier achat
    - F (Frequency) : nombre d'achats
    - M (Monetary) : montant total dépensé (en EUR)
    """
    snapshot_date = pd.to_datetime(df["invoice_date"]).max()
    
    # Agrégation par client
    rfm = df.groupby("customer_id").agg({
        "invoice_date": lambda x: (snapshot_date - pd.to_datetime(x).max()).days,
        "invoice_no": "count",
        "line_total": "sum"
    }).reset_index()
    
    rfm.columns = ["customer_id", "recency", "frequency", "monetary"]
    rfm["monetary"] = rfm["monetary"].astype(float) * exchange_rate
    
    # Scoring RFM (1-5 pour chaque métrique)
    rfm["r_score"] = (5 - pd.qcut(rfm["recency"], 5, labels=False, duplicates="drop")).astype(int) + 1
    rfm["f_score"] = (pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=False, duplicates="drop") + 1).astype(int)
    rfm["m_score"] = (pd.qcut(rfm["monetary"], 5, labels=False, duplicates="drop") + 1).astype(int)
    
    # Combinaison RFM Score (ex: 555 = Champion)
    rfm["rfm_score"] = rfm[["r_score", "f_score", "m_score"]].astype(str).agg("".join, axis=1)
    
    # Segmentation
    def segment_customer(row):
        """Segmente le client selon son score RFM"""
        r, f, m = row["r_score"], row["f_score"], row["m_score"]
        if r >= 4 and f >= 4:
            return "Champions"
        elif r >= 3 and f >= 3:
            return "Loyal Customers"
        elif r >= 4 and f >= 2:
            return "Potential Loyalists"
        elif r >= 3 and f >= 2:
            return "At Risk"
        elif r < 3 and f >= 4:
            return "Cant Lose Them"
        elif r < 3 and f >= 2:
            return "Hibernating"
        else:
            return "Others"
    
    rfm["segment"] = rfm.apply(segment_customer, axis=1)
    print("\n📊 Distribution des segments :")
    print(rfm["segment"].value_counts())
    
    return rfm

def write_to_mysql(rfm):
    """Écrit les résultats RFM dans la table rfm_results MySQL"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Créer la table si elle n'existe pas
    create_table_query = """
    CREATE TABLE IF NOT EXISTS rfm_results (
        customer_id VARCHAR(50) PRIMARY KEY,
        recency INT,
        frequency INT,
        monetary DECIMAL(10,2),
        r_score INT,
        f_score INT,
        m_score INT,
        rfm_score VARCHAR(10),
        segment VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    cursor.execute(create_table_query)
    
    # Vider la table (pour éviter les doublons)
    cursor.execute("TRUNCATE TABLE rfm_results")
    
    # Insérer les données
    insert_query = """
    INSERT INTO rfm_results 
    (customer_id, recency, frequency, monetary, r_score, f_score, m_score, rfm_score, segment)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    for idx, row in rfm.iterrows():
        cursor.execute(insert_query, tuple(row))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✓ {len(rfm)} résultats RFM écrits dans MySQL (table rfm_results)")

def save_to_csv(rfm):
    """Sauvegarde aussi en CSV pour le dashboard"""
    columns = ["customer_id", "recency", "frequency", "monetary", "r_score", "f_score", "m_score", "rfm_score", "segment"]
    rfm[columns].to_csv("rfm_results.csv", index=False)
    print(f"✓ {len(rfm)} segments sauvegardés dans rfm_results.csv")

def main():
    """Fonction principale du pipeline"""
    print("\n" + "="*60)
    print(" 🚀 PIPELINE RFM - SEGMENTATION CLIENTS E-COMMERCE")
    print("="*60 + "\n")
    
    # Étape 1 : Récupérer taux de change
    rate = get_exchange_rate()
    
    # Étape 2 : Charger données
    df = load_orders_data()
    
    # Étape 3 : Nettoyer
    df = clean_data(df)
    
    # Étape 4 : Calculer RFM
    print("\n📈 Calcul RFM en cours...")
    rfm = compute_rfm(df, exchange_rate=rate)
    
    # Étape 5 : Écrire dans MySQL
    print("\n💾 Écriture dans MySQL...")
    write_to_mysql(rfm)
    
    # Étape 6 : Sauvegarder en CSV
    save_to_csv(rfm)
    
    print("\n" + "="*60)
    print(" ✅ PIPELINE TERMINÉ AVEC SUCCÈS!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
