# Интеграция с Makefile для сохранения данных при пересборке

param (
    [switch]$Force = $false
)

# Функция для вывода цветного текста
function Write-ColorText {
    param (
        [string]$Text,
        [string]$Color = "White"
    )
    
    $Host.UI.WriteLine($Color, $Host.UI.RawUI.BackgroundColor, $Text)
}

Write-ColorText "=== Интеграция команд сохранения данных в Makefile ===" "Yellow"

# Проверка наличия файлов
if (-not (Test-Path "Makefile")) {
    Write-ColorText "❌ Файл Makefile не найден" "Red"
    exit 1
}

if (-not (Test-Path "Makefile.persistence")) {
    Write-ColorText "❌ Файл Makefile.persistence не найден" "Red"
    exit 1
}

# Создаем резервную копию оригинального Makefile
Write-Host "📑 Создание резервной копии Makefile..."
Copy-Item "Makefile" "Makefile.bak" -Force
Write-ColorText "✓ Резервная копия создана: Makefile.bak" "Green"

# Получаем содержимое файлов
$makefileContent = Get-Content -Path "Makefile" -Raw
$persistenceContent = Get-Content -Path "Makefile.persistence" -Raw

# Проверяем, не добавлены ли уже команды
if ($makefileContent -match "include Makefile.persistence") {
    if (-not $Force) {
        Write-ColorText "⚠️ Команды сохранения данных уже интегрированы в Makefile." "Yellow"
        Write-ColorText "Используйте параметр -Force для принудительной интеграции." "Yellow"
        exit 0
    } else {
        Write-ColorText "Выполняется принудительная интеграция..." "Yellow"
    }
}

# Добавляем include директиву в конец Makefile
Write-Host "📝 Добавление директивы include в Makefile..."
Add-Content -Path "Makefile" -Value "`n# Включение модуля сохранения данных при пересборке контейнеров"
Add-Content -Path "Makefile" -Value "include Makefile.persistence"

# Модифицируем раздел .PHONY для добавления новых команд
$makefileContent = Get-Content -Path "Makefile" -Raw
$newPhony = ".PHONY: help setup deploy update start stop restart rebuild logs logs-bot logs-db status backup restore check-db check-ml train-ml clean clean-all disk-usage backup-data restore-data update-safe rebuild-safe fix-persistence help-persistence"
$makefileContent = $makefileContent -replace "\.PHONY: help setup deploy update start stop restart rebuild logs logs-bot logs-db status backup restore check-db check-ml train-ml clean clean-all disk-usage", $newPhony

# Добавляем вызов help-persistence в команду help
$helpPattern = "(help:[^@]*@echo.*?Обслуживание.*?`n)"
$helpReplacement = '$1	@make help-persistence' + "`n"
$makefileContent = $makefileContent -replace $helpPattern, $helpReplacement

# Записываем изменения обратно в файл
Set-Content -Path "Makefile" -Value $makefileContent

Write-ColorText "✓ Makefile обновлен" "Green"
Write-ColorText "Теперь доступны следующие команды:" "Yellow"
Write-Host "  make backup-data   - Создание резервной копии данных регистрации"
Write-Host "  make restore-data  - Восстановление данных регистрации"
Write-Host "  make update-safe   - Обновление с сохранением данных регистрации"
Write-Host "  make rebuild-safe  - Пересборка с сохранением данных регистрации"
Write-Host "  make fix-persistence - Исправление проблемы сохранения данных"

Write-ColorText "`n=== Интеграция завершена ===" "Green"
Write-Host "Для применения изменений в продакшене выполните: make fix-persistence"
