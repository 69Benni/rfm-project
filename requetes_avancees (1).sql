-- ========================================================================
-- PROJET RFM - REQUÊTES SQL AVANCÉES
-- ========================================================================

USE ecommerce_rfm;

-- ========================================================================
-- REQUÊTE 1 : SELECT avec WHERE et ORDER BY
-- Objectif : Lister tous les clients avec leurs montants, triés par montant DESC
-- ========================================================================
SELECT 
    c.customer_id,
    c.country,
    SUM(oi.line_total) AS total_spent,
    COUNT(DISTINCT o.invoice_no) AS num_orders
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
LEFT JOIN order_items oi ON o.invoice_no = oi.invoice_no
WHERE c.customer_id IS NOT NULL
GROUP BY c.customer_id, c.country
ORDER BY total_spent DESC
LIMIT 10;

-- ========================================================================
-- REQUÊTE 2 : GROUP BY et HAVING
-- Objectif : Trouver les pays avec plus de 2 clients et montant total > 100
-- ========================================================================
SELECT 
    c.country,
    COUNT(DISTINCT c.customer_id) AS num_customers,
    SUM(oi.line_total) AS total_revenue
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
LEFT JOIN order_items oi ON o.invoice_no = oi.invoice_no
GROUP BY c.country
HAVING COUNT(DISTINCT c.customer_id) >= 2 
   AND SUM(oi.line_total) > 100
ORDER BY total_revenue DESC;

-- ========================================================================
-- REQUÊTE 3 : Jointure 3 tables + WHERE + ORDER BY + LIMIT
-- Objectif : Top 5 produits vendus par les clients loyalistes
-- ========================================================================
SELECT 
    oi.product_name,
    COUNT(oi.product_name) AS times_sold,
    SUM(oi.quantity) AS total_quantity,
    AVG(oi.unit_price) AS avg_price
FROM order_items oi
INNER JOIN orders o ON oi.invoice_no = o.invoice_no
INNER JOIN customers c ON o.customer_id = c.customer_id
WHERE o.invoice_date >= '2011-01-01'
GROUP BY oi.product_name
HAVING COUNT(oi.product_name) >= 2
ORDER BY times_sold DESC
LIMIT 5;

-- ========================================================================
-- REQUÊTE 4 : Sous-requête
-- Objectif : Clients qui ont dépensé PLUS que la moyenne
-- ========================================================================
SELECT 
    c.customer_id,
    c.country,
    SUM(oi.line_total) AS total_spent
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
LEFT JOIN order_items oi ON o.invoice_no = oi.invoice_no
GROUP BY c.customer_id, c.country
HAVING SUM(oi.line_total) > (
    SELECT AVG(total)
    FROM (
        SELECT SUM(line_total) AS total
        FROM order_items
        GROUP BY invoice_no
    ) subquery
)
ORDER BY total_spent DESC;

-- ========================================================================
-- REQUÊTE 5 : CTE (Common Table Expression)
-- Objectif : Ranking des clients par montant dépensé avec CTE
-- ========================================================================
WITH customer_spending AS (
    SELECT 
        c.customer_id,
        c.country,
        SUM(oi.line_total) AS total_spent,
        COUNT(DISTINCT o.invoice_no) AS num_orders
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    LEFT JOIN order_items oi ON o.invoice_no = oi.invoice_no
    GROUP BY c.customer_id, c.country
),
ranked_customers AS (
    SELECT 
        customer_id,
        country,
        total_spent,
        num_orders,
        ROW_NUMBER() OVER (ORDER BY total_spent DESC) AS rank
    FROM customer_spending
)
SELECT * FROM ranked_customers
WHERE rank <= 10;

-- ========================================================================
-- CRÉER UNE VUE : Vue RFM simplifiée
-- Objectif : Vue contenant les données RFM pour chaque client
-- ========================================================================
CREATE OR REPLACE VIEW v_customer_rfm AS
SELECT 
    c.customer_id,
    c.country,
    MAX(o.invoice_date) AS last_order_date,
    DATEDIFF('2011-12-31', MAX(o.invoice_date)) AS recency_days,
    COUNT(DISTINCT o.invoice_no) AS frequency,
    SUM(oi.line_total) AS monetary_value,
    ROUND(SUM(oi.line_total) / COUNT(DISTINCT o.invoice_no), 2) AS avg_order_value
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
LEFT JOIN order_items oi ON o.invoice_no = oi.invoice_no
WHERE c.customer_id IS NOT NULL
GROUP BY c.customer_id, c.country;

-- Test de la vue
SELECT * FROM v_customer_rfm LIMIT 10;

-- ========================================================================
-- FONCTION STOCKÉE : Calculer le RFM Score
-- Objectif : Fonction qui retourne le score RFM d'un client
-- ========================================================================
DELIMITER //

CREATE FUNCTION calculate_rfm_score(
    p_recency INT,
    p_frequency INT,
    p_monetary DECIMAL(10,2)
) RETURNS INT DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE r_score INT;
    DECLARE f_score INT;
    DECLARE m_score INT;
    DECLARE rfm_score INT;
    
    -- Calculer R Score (1-5)
    IF p_recency <= 30 THEN SET r_score = 5;
    ELSEIF p_recency <= 60 THEN SET r_score = 4;
    ELSEIF p_recency <= 90 THEN SET r_score = 3;
    ELSEIF p_recency <= 120 THEN SET r_score = 2;
    ELSE SET r_score = 1;
    END IF;
    
    -- Calculer F Score (1-5)
    IF p_frequency >= 5 THEN SET f_score = 5;
    ELSEIF p_frequency >= 4 THEN SET f_score = 4;
    ELSEIF p_frequency >= 3 THEN SET f_score = 3;
    ELSEIF p_frequency >= 2 THEN SET f_score = 2;
    ELSE SET f_score = 1;
    END IF;
    
    -- Calculer M Score (1-5)
    IF p_monetary >= 150 THEN SET m_score = 5;
    ELSEIF p_monetary >= 100 THEN SET m_score = 4;
    ELSEIF p_monetary >= 50 THEN SET m_score = 3;
    ELSEIF p_monetary >= 20 THEN SET m_score = 2;
    ELSE SET m_score = 1;
    END IF;
    
    -- Combiner en RFM Score
    SET rfm_score = CONCAT(r_score, f_score, m_score);
    
    RETURN rfm_score;
END //

DELIMITER ;

-- Test de la fonction
SELECT 
    customer_id,
    recency_days,
    frequency,
    monetary_value,
    calculate_rfm_score(recency_days, frequency, monetary_value) AS rfm_score
FROM v_customer_rfm
LIMIT 10;

-- ========================================================================
-- PROCÉDURE STOCKÉE : Mettre à jour les segments RFM
-- ========================================================================
DELIMITER //

CREATE PROCEDURE update_customer_segments()
BEGIN
    UPDATE rfm_segments rs
    SET rs.r_score = CASE 
            WHEN (SELECT recency_days FROM v_customer_rfm v WHERE v.customer_id = rs.customer_id) <= 30 THEN 5
            WHEN (SELECT recency_days FROM v_customer_rfm v WHERE v.customer_id = rs.customer_id) <= 60 THEN 4
            WHEN (SELECT recency_days FROM v_customer_rfm v WHERE v.customer_id = rs.customer_id) <= 90 THEN 3
            WHEN (SELECT recency_days FROM v_customer_rfm v WHERE v.customer_id = rs.customer_id) <= 120 THEN 2
            ELSE 1
        END
    WHERE rs.customer_id IN (SELECT customer_id FROM v_customer_rfm);
END //

DELIMITER ;

-- Appeler la procédure
CALL update_customer_segments();
