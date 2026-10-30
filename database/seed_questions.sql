USE ai_interviewer;

-- Helper macro insertion for Topic 4 (Basic Queries & Joins)
INSERT INTO questions (id, topic_id, question_text, difficulty, explanation, source) VALUES
(1, 4, 'Which SQL keyword is used to retrieve unique records from a database table?', 'basic', 'The DISTINCT keyword eliminates duplicate rows from the query output.', 'manual'),
(2, 4, 'Which type of SQL JOIN returns all records when there is a match in either left or right table?', 'intermediate', 'FULL OUTER JOIN combines the results of both left and right outer joins.', 'manual'),
(3, 4, 'In SQL execution order, which clause is evaluated directly AFTER the WHERE clause?', 'advanced', 'SQL execution sequence order is FROM -> WHERE -> GROUP BY -> HAVING -> SELECT.', 'manual');

INSERT INTO question_options (question_id, option_text, is_correct) VALUES
(1, 'UNIQUE', FALSE), (1, 'DISTINCT', TRUE), (1, 'DIFFERENT', FALSE), (1, 'GROUP BY', FALSE),
(2, 'INNER JOIN', FALSE), (2, 'LEFT JOIN', FALSE), (2, 'FULL OUTER JOIN', TRUE), (2, 'CROSS JOIN', FALSE),
(3, 'HAVING', FALSE), (3, 'SELECT', FALSE), (3, 'GROUP BY', TRUE), (3, 'ORDER BY', FALSE);

-- Helper insertion for Topic 5 (Subqueries & Aggregations)
INSERT INTO questions (id, topic_id, question_text, difficulty, explanation, source) VALUES
(4, 5, 'Which aggregate function counts non-NULL values in a specified column?', 'basic', 'COUNT(column_name) ignores NULL values in its calculation.', 'manual'),
(5, 5, 'When using GROUP BY, which clause must be used to filter aggregated group results?', 'intermediate', 'The HAVING clause filters rows after aggregation, whereas WHERE filters before aggregation.', 'manual'),
(6, 5, 'What sets a Correlated Subquery apart from an Uncorrelated Subquery?', 'advanced', 'A correlated subquery references columns from the outer query and re-evaluates for every row processed.', 'manual');

INSERT INTO question_options (question_id, option_text, is_correct) VALUES
(4, 'SUM()', FALSE), (4, 'COUNT()', TRUE), (4, 'TOTAL()', FALSE), (4, 'MAX()', FALSE),
(5, 'WHERE', FALSE), (5, 'HAVING', TRUE), (5, 'FILTER', FALSE), (5, 'LIMIT', FALSE),
(6, 'It runs only once before the main query', FALSE), (6, 'It relies on outer query values for each row execution', TRUE), (6, 'It returns multi-column results exclusively', FALSE), (6, 'It requires temporary staging tables', FALSE);