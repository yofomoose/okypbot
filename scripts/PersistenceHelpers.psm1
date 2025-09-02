# Дополнение к Makefile для OkypBot с Powershell
# Эта команда позволяет безопасно обновлять бот с сохранением данных регистрации

# Цвета для PowerShell
$GREEN = "Green"
$RED = "Red"
$YELLOW = "Yellow"
$NC = "White"

function Write-ColorOutput($Text, $Color) {
    Write-Host $Text -ForegroundColor $Color
}

# Команда для отображения справки по новым командам
function Show-PersistenceHelp {
    Write-Host ""
    Write-ColorOutput "Команды для сохранения данных регистрации:" $YELLOW
    Write-Host "  .\scripts\Save-RegistrationData.ps1       - Создание резервной копии данных регистрации"
    Write-Host "  .\scripts\Restore-RegistrationData.ps1    - Восстановление данных регистрации"
    Write-Host "  .\scripts\Update-BotSafely.ps1            - Обновление с сохранением данных регистрации"
    Write-Host "  .\scripts\Rebuild-BotSafely.ps1           - Пересборка с сохранением данных регистрации"
    Write-Host "  .\scripts\Fix-DataPersistence.ps1         - Исправление проблемы сохранения данных"
}

# Экспортируем функцию, чтобы её можно было использовать из других скриптов
Export-ModuleMember -Function Show-PersistenceHelp
