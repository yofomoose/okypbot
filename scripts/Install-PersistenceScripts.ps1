# Интеграция с Makefile для сохранения данных регистрации
# Install-PersistenceScripts.ps1

Write-Host "=== Установка скриптов для решения проблемы сохранения данных ===" -ForegroundColor Cyan

# Проверка наличия созданных файлов
$requiredScripts = @(
    "PersistenceHelpers.psm1",
    "Save-RegistrationData.ps1",
    "Restore-RegistrationData.ps1", 
    "Update-BotSafely.ps1",
    "Rebuild-BotSafely.ps1",
    "Fix-DataPersistence.ps1"
)

$allFilesExist = $true
foreach ($script in $requiredScripts) {
    $scriptPath = Join-Path "scripts" $script
    if (-not (Test-Path $scriptPath)) {
        Write-Host "❌ Файл $scriptPath не найден!" -ForegroundColor Red
        $allFilesExist = $false
    }
}

if (-not $allFilesExist) {
    Write-Host "❌ Некоторые скрипты отсутствуют. Установка прервана." -ForegroundColor Red
    exit 1
}

# Проверяем права доступа для выполнения скриптов
Write-Host "Настройка прав доступа для скриптов..." -ForegroundColor Yellow
foreach ($script in $requiredScripts) {
    $scriptPath = Join-Path "scripts" $script
    try {
        if (Test-Path $scriptPath) {
            # Для Windows не требуется chmod, но можно проверить блокировку файла
            Unblock-File -Path $scriptPath -ErrorAction SilentlyContinue
            Write-Host "✓ Права настроены для $script" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠️ Не удалось настроить права для $script: $_" -ForegroundColor Yellow
    }
}

# Создание документации
$docsContent = @"
# Решение проблемы сохранения данных регистрации при пересборке контейнера

## Проблема

При пересборке Docker-контейнеров теряются данные регистрации пользователей, и пользователям приходится регистрироваться заново.

## Решение

Разработан набор PowerShell-скриптов для безопасного обновления и пересборки контейнеров с сохранением данных регистрации.

## Доступные скрипты

| Скрипт | Описание |
|--------|----------|
| `Save-RegistrationData.ps1` | Создание резервной копии данных регистрации |
| `Restore-RegistrationData.ps1` | Восстановление данных регистрации |
| `Update-BotSafely.ps1` | Обновление бота с сохранением данных регистрации |
| `Rebuild-BotSafely.ps1` | Пересборка контейнера с сохранением данных регистрации |
| `Fix-DataPersistence.ps1` | Полное исправление проблемы сохранения данных |

## Использование

### Обновление бота с сохранением данных

```powershell
.\scripts\Update-BotSafely.ps1
```

### Пересборка контейнера с сохранением данных

```powershell
.\scripts\Rebuild-BotSafely.ps1
```

### Однократное исправление проблемы

```powershell
.\scripts\Fix-DataPersistence.ps1
```

## Рекомендации

1. Всегда используйте скрипт `Update-BotSafely.ps1` вместо прямого вызова `docker-compose`
2. Регулярно делайте резервные копии с помощью `Save-RegistrationData.ps1`
3. После критических изменений проверяйте целостность данных

## Техническая информация

Скрипты работают следующим образом:
1. Создание резервной копии данных перед обновлением
2. Выполнение обновления или пересборки контейнера
3. Восстановление данных в новый контейнер
4. Настройка прав доступа для корректной работы

## Решаемые проблемы

- Сохранение данных пользователей (`users.json`)
- Сохранение информации о заявках (`user_issues.json`)
- Сохранение сопоставлений сотрудников (`employee_mapping.json`)
"@

$docsPath = "docs\powershell_scripts_guide.md"
Set-Content -Path $docsPath -Value $docsContent
Write-Host "✓ Создана документация: $docsPath" -ForegroundColor Green

# Создание примера скрипта для запуска
$launcherPath = "UpdateBot.ps1"
$launcherContent = @"
# Запуск безопасного обновления бота
Write-Host "Запуск безопасного обновления бота..." -ForegroundColor Cyan
.\scripts\Update-BotSafely.ps1
"@
Set-Content -Path $launcherPath -Value $launcherContent
Write-Host "✓ Создан скрипт быстрого запуска: $launcherPath" -ForegroundColor Green

Write-Host "=== Установка завершена ===" -ForegroundColor Green
Write-Host "Для обновления бота с сохранением данных выполните:" -ForegroundColor Cyan
Write-Host "    .\UpdateBot.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "Или воспользуйтесь одним из скриптов в папке scripts:" -ForegroundColor Cyan
Write-Host "    .\scripts\Update-BotSafely.ps1    - Обновление бота" -ForegroundColor Yellow
Write-Host "    .\scripts\Rebuild-BotSafely.ps1   - Пересборка контейнера" -ForegroundColor Yellow
Write-Host "    .\scripts\Fix-DataPersistence.ps1 - Исправление проблемы сохранения данных" -ForegroundColor Yellow
