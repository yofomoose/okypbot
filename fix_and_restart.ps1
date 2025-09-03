#!/usr/bin/env pwsh

# Скрипт для исправления и перезапуска бота с фиксами

Write-Host "🔧 Применяем исправления для бота..." -ForegroundColor Yellow

# Переходим в корневую директорию проекта
Set-Location $PSScriptRoot

Write-Host "📊 Проверяем текущее состояние контейнеров..." -ForegroundColor Cyan
docker compose ps

Write-Host "🛑 Останавливаем контейнер приложения..." -ForegroundColor Yellow
docker compose stop app

Write-Host "🗑️ Удаляем старый контейнер..." -ForegroundColor Yellow
docker compose rm -f app

Write-Host "🔨 Пересобираем образ с исправлениями..." -ForegroundColor Cyan
docker compose build --no-cache app

Write-Host "🚀 Запускаем исправленный контейнер..." -ForegroundColor Green
docker compose up -d app

Write-Host "⏳ Ждем запуска приложения (10 секунд)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "📊 Проверяем статус контейнеров..." -ForegroundColor Cyan
docker compose ps

Write-Host "📋 Показываем последние логи..." -ForegroundColor Cyan
docker compose logs --tail=20 app

Write-Host "✅ Исправления применены! Проверьте работу бота командой /start" -ForegroundColor Green
Write-Host "📝 Для просмотра полных логов: docker compose logs -f app" -ForegroundColor Blue
