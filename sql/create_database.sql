-- Создание базы данных okypbot для PostgreSQL
-- В pgAdmin выполните эти команды по отдельности:

-- 1. Создание базы данных (выполнить отдельно)
-- Правой кнопкой на "Databases" -> Create -> Database...
-- Имя: okypbot
-- Владелец: postgres
-- Кодировка: UTF8

-- ИЛИ выполните эту команду в psql (не в pgAdmin Query Tool):
-- CREATE DATABASE okypbot WITH OWNER = postgres ENCODING = 'UTF8';

-- 2. После создания БД подключитесь к ней и выполните:
-- Создание расширений для полнотекстового поиска (опционально)
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- CREATE EXTENSION IF NOT EXISTS unaccent;

-- 3. Проверка создания
SELECT current_database() as database_name, current_user as current_user;
