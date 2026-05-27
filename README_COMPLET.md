# 📊 RFM Segmentation Project

## Projet Final - Algo & Bases de Données
**MSc2 Manager Data Marketing - INSEEC Lyon**  
**Deadline: 28 mai 2026**

---

## 🎯 PROBLÉMATIQUE MÉTIER

### Contexte
Une boutique en ligne UK vend à des milliers de clients. Cependant, tous les clients ne sont pas égaux en termes de :
- Fréquence d'achat
- Montant dépensé
- Engagement récent

### Challenge
Comment **segmenter les clients** pour adapter la stratégie marketing ?

### Solution
**Segmentation RFM** : Identifier les 8 segments de clients basés sur trois critères :
- **R** (Recency) : Combien de jours depuis le dernier achat ?
- **F** (Frequency) : Combien de fois le client a-t-il acheté ?
- **M** (Monetary) : Combien a-t-il dépensé en total ?

### Objectifs
✅ Identifier les Champions (top clients à fidéliser)  
✅ Repérer les clients à risque (à reconquérir)  
✅ Cibler les potentiels loyalistes (à convertir)  
✅ Optimiser l'allocation du budget marketing  

---

## 📈 RÉSULTATS CLÉS

### Distribution des segments (32 clients)
| Segment | Nombre | % | Action |
|---------|--------|----|----|
| **Loyal Customers** | 11 | 34.4% | Fidéliser |
| **Champions** | 8 | 25% | Récompenser |
| **Others** | 7 | 21.9% | Ignorer |
| **Potential Loyalists** | 5 | 15.6% | Convertir |
| **At Risk** | 1 | 3.1% | Reconquérir |

### Insights
- Les **Loyal Customers** génèrent **50%+ du chiffre d'affaires**
- Le client moyen ne revient que tous les **89.6 jours**
- Dépense moyenne : **€96 (convertie depuis GBP)**

---

## 🏗️ ARCHITECTURE TECHNIQUE

### 1️⃣ Modélisation & Bases de Données (Partie 1)

#### Schéma ER (dbdiagram.io)
```
customers (1) ─── (n) orders
orders (1) ─── (n) order_items
```

#### Tables
- **customers** : customer_id, country
- **orders** : invoice_no, customer_id, invoice_date
- **order_items** : invoice_no, product_name, quantity, unit_price, line_total
- **rfm_results** : Résultats RFM finaux

#### Contraintes SQL
✅ FOREIGN KEY (orders.customer_id → customers.customer_id)  
✅ NOT NULL sur customer_id, invoice_date  
✅ UNIQUE sur invoice_no  

#### Requêtes SQL Avancées

**1. SELECT + WHERE + ORDER BY + LIMIT**
```sql
SELECT customer_id, country, SUM(line_total) AS total
FROM orders o
LEFT JOIN order_items oi ON o.invoice_no = oi.invoice_no
WHERE customer_id IS NOT NULL
ORDER BY total DESC
LIMIT 10;
```

**2. GROUP BY + HAVING**
```sql
SELECT country, COUNT(DISTINCT customer_id) AS num_customers
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY country
HAVING COUNT(DISTINCT customer_id) >= 2
ORDER BY num_customers DESC;
```

**3. Jointure 3+ tables**
```sql
SELECT oi.product_name, COUNT(*) AS times_sold
FROM order_items oi
INNER JOIN orders o ON oi.invoice_no = o.invoice_no
INNER JOIN customers c ON o.customer_id = c.customer_id
WHERE o.invoice_date >= '2011-01-01'
GROUP BY oi.product_name
LIMIT 5;
```

**4. Sous-requête**
```sql
SELECT customer_id, SUM(oi.line_total) AS total
FROM orders o
LEFT JOIN order_items oi ON o.invoice_no = oi.invoice_no
GROUP BY customer_id
HAVING SUM(oi.line_total) > (
    SELECT AVG(total_spent) FROM (
        SELECT SUM(line_total) AS total_spent FROM order_items GROUP BY invoice_no
    ) subquery
);
```

**5. CTE (Common Table Expression)**
```sql
WITH customer_spending AS (
    SELECT customer_id, SUM(line_total) AS total
    FROM orders o
    LEFT JOIN order_items oi ON o.invoice_no = oi.invoice_no
    GROUP BY customer_id
)
SELECT * FROM customer_spending
WHERE total > 100
ORDER BY total DESC;
```

#### Vues & Fonctions
✅ **VUE** : `v_customer_rfm` (données RFM par client)  
✅ **FONCTION** : `calculate_rfm_score()` (scoring RFM 1-5)  
✅ **PROCÉDURE** : `update_customer_segments()` (mise à jour segments)  

### 2️⃣ Pipeline Python (Partie 2)

#### Pipeline ETL
```python
pipeline.py
├── load_orders_data()     # Charge depuis MySQL
├── get_exchange_rate()    # API ExchangeRate (GBP → EUR)
├── compute_rfm()          # Calcul RFM + scoring
├── write_to_mysql()       # Écriture dans rfm_results
└── save_to_csv()          # Sauvegarde locale
```

#### Étapes
1. **Connexion MySQL** : Récupère 82 lignes de transactions
2. **Enrichissement API** : Convertit GBP → EUR (taux dynamique)
3. **Calcul RFM** :
   - Recency = jours depuis dernier achat
   - Frequency = nombre de commandes
   - Monetary = montant total dépensé
4. **Scoring** : Chaque métrique notée 1-5
5. **Segmentation** : 8 segments selon seuils RFM
6. **Écriture MySQL** : Table `rfm_results`

#### Technologies
- `pandas` : Transformation données
- `mysql.connector` : Connexion MySQL
- `requests` : Appel API ExchangeRate
- `.env` : Gestion credentials (sécurisé)

### 3️⃣ Dashboard Interactif (Partie 3)

#### Composants
✅ **3 KPIs** :
- Total Customers
- Avg Recency (jours)
- Avg Revenue (€)

✅ **3 Graphiques** :
- Pie chart : Distribution segments
- Bar chart : Revenue par segment
- Scatter plot : Recency vs Monetary (taille = Frequency)

✅ **1 Filtre interactif** :
- Dropdown pour filtrer par segment
- Mise à jour dynamique des KPIs & graphiques

✅ **1 Callback** :
```python
@app.callback(
    [Output("pie", "figure"), Output("bar", "figure"), ...],
    Input("segment-filter", "value")  # ← Filtre
)
```

#### Frameworks
- `Plotly` : Visualisation interactive
- `Dash` : Framework web
- `Python 3.13`

---

## 🚀 INSTALLATION & UTILISATION

### 1. Cloner le projet
```bash
git clone https://github.com/[USERNAME]/rfm-project.git
cd rfm-project
```

### 2. Créer l'environnement virtuel
```bash
python -m venv .venv
.venv\Scripts\Activate  # Windows
source .venv/bin/activate  # Mac/Linux
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configurer MySQL
Crée un fichier `.env` à la racine :
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=ton_mot_de_passe
DB_NAME=ecommerce_rfm
DB_PORT=3306
```

### 5. Charger la base de données
```bash
mysql -u root -p < schema.sql
# Entrer le mot de passe
```

### 6. Lancer le pipeline
```bash
python pipeline.py
# Output: ✓ 82 lignes chargées
# Output: ✓ 32 segments sauvegardés dans rfm_results.csv
# Output: ✓ Résultats écrits dans MySQL (table rfm_results)
```

### 7. Lancer le dashboard
```bash
python app.py
# Output: Dash is running on http://0.0.0.0:8050/
```

### 8. Accéder au dashboard
Ouvre **http://localhost:8050** dans ton navigateur

### 9. Utiliser le filtre
- Sélectionne un segment dans le dropdown
- Les graphiques se mettent à jour automatiquement ✨

---

## 📁 STRUCTURE DU PROJET

```
rfm-project/
├── app.py                 # Dashboard Dash avec filtre interactif
├── pipeline.py            # Pipeline ETL (load → RFM → MySQL)
├── test_connection.py     # Test connexion MySQL
├── rfm_results.csv        # Résultats RFM (généré automatiquement)
├── schema.sql             # Script SQL (5 requêtes, vue, fonction, procédure)
├── requetes_avancees.sql  # Requêtes SQL détaillées
├── requirements.txt       # Dépendances Python
├── .env                   # Credentials (⚠️ NE PAS committer)
├── .gitignore             # Exclut .env, .venv, etc.
└── README.md              # Cette documentation
```

---

## 📊 SCHÉMA DBDIAGRAM.IO

```
Customers (32 clients)
├── customer_id (PK)
└── country

Orders (82 transactions)
├── invoice_no (PK)
├── customer_id (FK)
└── invoice_date

OrderItems (82 lignes)
├── invoice_no (FK)
├── product_name
├── quantity
├── unit_price
└── line_total

RFM_Results (32 segments)
├── customer_id (PK)
├── recency (jours)
├── frequency (achats)
├── monetary (€)
├── r_score (1-5)
├── f_score (1-5)
├── m_score (1-5)
├── rfm_score (ex: 555)
└── segment (ex: Champions)
```

---

## 🔐 Sécurité

⚠️ **Fichiers sensibles (NE PAS committer)** :
- `.env` → Contient mot de passe MySQL
- `.venv/` → Dépendances locales
- `__pycache__/` → Cache Python

✅ **Fichier `.gitignore`** :
```
.env
.venv/
__pycache__/
*.pyc
rfm_results.csv
```

---

## 📚 Ressources

- **Dataset** : Online Retail II (Kaggle)
- **Technologies** : MySQL 8.0, Python 3.13, Plotly Dash
- **Concepts** : RFM Analysis, ETL Pipeline, Interactive Dashboards

---

## ✍️ Auteur

**Yass** - INSEEC Lyon, MSc2 Manager Data Marketing (2026)

---

## 📝 Licence

Projet académique - Libre d'utilisation à titre éducatif.
