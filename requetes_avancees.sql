-- ===== RELATION MANY-TO-MANY =====

-- Créer la table tags
CREATE TABLE tags (
  tag_id INT PRIMARY KEY AUTO_INCREMENT,
  tag_name VARCHAR(100) NOT NULL UNIQUE
);

-- Créer la relation many-to-many
CREATE TABLE customer_tags (
  customer_id INT NOT NULL,
  tag_id INT NOT NULL,
  PRIMARY KEY (customer_id, tag_id),
  FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
  FOREIGN KEY (tag_id) REFERENCES tags(tag_id)
);

-- Ajouter quelques tags
INSERT INTO tags (tag_name) VALUES 
('VIP'),
('Premium'),
('Régulier'),
('Nouveau'),
('Inactif');

-- Assigner des tags aux clients
INSERT INTO customer_tags (customer_id, tag_id) VALUES 
(1, 1),
(1, 2),
(2, 3),
(3, 4),
(5, 5);