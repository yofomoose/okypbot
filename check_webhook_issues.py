#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для проверки и исправления проблем с веб-хуком
"""

import logging
import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebhookAnalyzer:
    """Анализатор веб-хука для диагностики проблем"""
    
    def __init__(self, base_url: str = None):
        """
        Инициализация анализатора веб-хука
        
        Args:
            base_url (str): Базовый URL для проверки. Если None, используется локальный хост.
        """
        self.base_url = base_url or "http://localhost:8000"
        self.base_url = self.base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 10
    
    def check_config(self) -> Dict[str, Any]:
        """
        Проверка конфигурации веб-хука
        
        Returns:
            Dict[str, Any]: Результаты проверки конфигурации
        """
        print("\n🔍 Проверка конфигурации веб-хука...")
        
        try:
            # Импортируем конфигурацию
            import config
            
            # Проверяем наличие и значения необходимых переменных
            webhook_enabled = getattr(config, 'WEBHOOK_ENABLED', None)
            webhook_host = getattr(config, 'WEBHOOK_HOST', None)
            webhook_port = getattr(config, 'WEBHOOK_PORT', None)
            okdesk_webhook_secret = getattr(config, 'OKDESK_WEBHOOK_SECRET', None)
            okdesk_api_token = getattr(config, 'OKDESK_API_TOKEN', None)
            okdesk_base_url = getattr(config, 'OKDESK_BASE_URL', None)
            
            results = {
                "webhook_enabled": {
                    "value": webhook_enabled,
                    "status": "ok" if webhook_enabled is not None else "missing"
                },
                "webhook_host": {
                    "value": webhook_host,
                    "status": "ok" if webhook_host else "missing"
                },
                "webhook_port": {
                    "value": webhook_port,
                    "status": "ok" if webhook_port else "missing"
                },
                "okdesk_webhook_secret": {
                    "value": "***" if okdesk_webhook_secret else None,
                    "status": "ok" if okdesk_webhook_secret else "missing"
                },
                "okdesk_api_token": {
                    "value": "***" if okdesk_api_token else None,
                    "status": "ok" if okdesk_api_token else "missing"
                },
                "okdesk_base_url": {
                    "value": okdesk_base_url,
                    "status": "ok" if okdesk_base_url else "missing"
                }
            }
            
            # Выводим результаты проверки
            print("\n📋 Результаты проверки конфигурации:")
            
            for key, data in results.items():
                status_icon = "✅" if data["status"] == "ok" else "❌"
                value = data["value"] if data["value"] is not None else "Не задано"
                print(f"{status_icon} {key}: {value}")
            
            return results
            
        except ImportError:
            print("❌ Ошибка импорта модуля конфигурации")
            return {
                "error": "import_error",
                "message": "Не удалось импортировать модуль конфигурации"
            }
        except Exception as e:
            print(f"❌ Ошибка проверки конфигурации: {e}")
            return {
                "error": str(e),
                "message": "Ошибка проверки конфигурации"
            }
    
    def check_webhook_server(self) -> Dict[str, Any]:
        """
        Проверка файла веб-хук сервера на наличие и корректность кода
        
        Returns:
            Dict[str, Any]: Результаты проверки
        """
        print("\n🔍 Проверка файла webhook_server.py...")
        
        webhook_server_path = Path("services/webhook_server.py")
        
        try:
            if not webhook_server_path.exists():
                print("❌ Файл webhook_server.py не найден")
                return {
                    "status": "missing",
                    "message": "Файл webhook_server.py не найден"
                }
            
            # Читаем содержимое файла
            with open(webhook_server_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Проверяем наличие критически важных компонентов
            checks = {
                "fastapi_import": "from fastapi import" in content,
                "app_definition": "app = FastAPI" in content,
                "verify_signature": "verify_signature" in content,
                "okdesk_webhook": "/okdesk-webhook" in content or "/webhook" in content,
                "handle_comment": "handle_comment" in content or "process_comment" in content
            }
            
            # Дополнительные проверки
            lines = content.splitlines()
            error_handling = any("except" in line and "HTTPException" in line for line in lines)
            logging_present = any("logger" in line and "info" in line for line in lines)
            
            checks["error_handling"] = error_handling
            checks["logging"] = logging_present
            
            # Выводим результаты проверки
            print("\n📋 Результаты проверки webhook_server.py:")
            
            all_passed = True
            for key, passed in checks.items():
                status_icon = "✅" if passed else "❌"
                all_passed = all_passed and passed
                print(f"{status_icon} {key}")
            
            return {
                "status": "ok" if all_passed else "issues",
                "checks": checks,
                "file_size": os.path.getsize(webhook_server_path)
            }
            
        except Exception as e:
            print(f"❌ Ошибка проверки webhook_server.py: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def test_webhook_endpoints(self) -> Dict[str, Any]:
        """
        Тестирование эндпоинтов веб-хука
        
        Returns:
            Dict[str, Any]: Результаты тестирования
        """
        print(f"\n🔍 Тестирование эндпоинтов веб-хука на {self.base_url}...")
        
        results = {}
        
        # Проверка health эндпоинта
        try:
            url = f"{self.base_url}/health"
            print(f"GET {url}")
            
            response = self.session.get(url)
            results["health"] = {
                "status": response.status_code,
                "response": response.json() if response.ok else None,
                "error": None
            }
            
            if response.ok:
                print(f"✅ Health эндпоинт: {response.status_code}")
            else:
                print(f"❌ Health эндпоинт: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка проверки health эндпоинта: {e}")
            results["health"] = {
                "status": None,
                "response": None,
                "error": str(e)
            }
            
        # Проверка webhook эндпоинта (HEAD запрос)
        try:
            url = f"{self.base_url}/okdesk-webhook"
            print(f"HEAD {url}")
            
            response = self.session.head(url)
            results["webhook_head"] = {
                "status": response.status_code,
                "headers": dict(response.headers),
                "error": None
            }
            
            if response.ok or response.status_code == 405:  # OK или Method Not Allowed
                print(f"✅ Webhook эндпоинт (HEAD): {response.status_code}")
            else:
                print(f"❌ Webhook эндпоинт (HEAD): {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка проверки webhook эндпоинта (HEAD): {e}")
            results["webhook_head"] = {
                "status": None,
                "headers": None,
                "error": str(e)
            }
            
        # Проверка корневого эндпоинта
        try:
            url = f"{self.base_url}/"
            print(f"GET {url}")
            
            response = self.session.get(url)
            results["root"] = {
                "status": response.status_code,
                "response": response.json() if response.ok and response.headers.get('content-type') == 'application/json' else None,
                "error": None
            }
            
            if response.ok:
                print(f"✅ Корневой эндпоинт: {response.status_code}")
            else:
                print(f"❌ Корневой эндпоинт: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка проверки корневого эндпоинта: {e}")
            results["root"] = {
                "status": None,
                "response": None,
                "error": str(e)
            }
            
        return results
    
    def check_docker_setup(self) -> Dict[str, Any]:
        """
        Проверка настройки Docker
        
        Returns:
            Dict[str, Any]: Результаты проверки
        """
        print("\n🔍 Проверка настройки Docker...")
        
        docker_compose_files = [
            Path("docker/docker-compose.prod.yml"),
            Path("docker/docker-compose.yml"),
            Path("docker-compose.yml")
        ]
        
        dockerfile_path = Path("docker/Dockerfile")
        
        results = {
            "docker_compose": None,
            "dockerfile": None
        }
        
        # Проверка docker-compose файла
        for path in docker_compose_files:
            if path.exists():
                print(f"✅ Найден docker-compose файл: {path}")
                
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Проверка наличия необходимых сервисов
                    has_app = "app:" in content
                    has_nginx = "nginx:" in content
                    has_ports = "ports:" in content
                    
                    results["docker_compose"] = {
                        "file": str(path),
                        "has_app": has_app,
                        "has_nginx": has_nginx,
                        "has_ports": has_ports,
                        "size": os.path.getsize(path)
                    }
                    
                    print(f"  - App сервис: {'✅' if has_app else '❌'}")
                    print(f"  - Nginx: {'✅' if has_nginx else '❌'}")
                    print(f"  - Порты: {'✅' if has_ports else '❌'}")
                    
                    break
                except Exception as e:
                    print(f"❌ Ошибка чтения docker-compose файла: {e}")
        
        # Если docker-compose файл не найден
        if results["docker_compose"] is None:
            print("❌ Docker-compose файл не найден")
            results["docker_compose"] = {
                "file": None,
                "error": "Docker-compose файл не найден"
            }
        
        # Проверка Dockerfile
        if dockerfile_path.exists():
            print(f"✅ Найден Dockerfile: {dockerfile_path}")
            
            try:
                with open(dockerfile_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Проверка наличия необходимых инструкций
                has_python = "FROM python" in content
                has_requirements = "requirements.txt" in content
                has_expose = "EXPOSE" in content
                
                results["dockerfile"] = {
                    "file": str(dockerfile_path),
                    "has_python": has_python,
                    "has_requirements": has_requirements,
                    "has_expose": has_expose,
                    "size": os.path.getsize(dockerfile_path)
                }
                
                print(f"  - Python: {'✅' if has_python else '❌'}")
                print(f"  - Requirements: {'✅' if has_requirements else '❌'}")
                print(f"  - Expose ports: {'✅' if has_expose else '❌'}")
                
            except Exception as e:
                print(f"❌ Ошибка чтения Dockerfile: {e}")
        else:
            print(f"❌ Dockerfile не найден: {dockerfile_path}")
            results["dockerfile"] = {
                "file": None,
                "error": "Dockerfile не найден"
            }
        
        return results

    def generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """
        Генерация рекомендаций на основе результатов проверок
        
        Args:
            results (Dict[str, Any]): Результаты проверок
            
        Returns:
            List[str]: Список рекомендаций
        """
        recommendations = []
        
        # Проверка конфигурации
        if "config" in results:
            config = results["config"]
            
            # Проверяем WEBHOOK_ENABLED
            if config.get("webhook_enabled", {}).get("status") == "missing":
                recommendations.append(
                    "Добавьте переменную WEBHOOK_ENABLED=True в конфигурацию для включения веб-хука"
                )
            
            # Проверяем WEBHOOK_HOST и WEBHOOK_PORT
            if config.get("webhook_host", {}).get("status") == "missing":
                recommendations.append(
                    "Добавьте переменную WEBHOOK_HOST в конфигурацию (например, '0.0.0.0')"
                )
            
            if config.get("webhook_port", {}).get("status") == "missing":
                recommendations.append(
                    "Добавьте переменную WEBHOOK_PORT в конфигурацию (например, 8000)"
                )
                
            # Проверяем секрет веб-хука
            if config.get("okdesk_webhook_secret", {}).get("status") == "missing":
                recommendations.append(
                    "Добавьте переменную OKDESK_WEBHOOK_SECRET для безопасной верификации запросов"
                )
        
        # Проверка файла webhook_server.py
        if "webhook_server" in results:
            webhook_server = results["webhook_server"]
            
            if webhook_server.get("status") == "missing":
                recommendations.append(
                    "Создайте файл services/webhook_server.py для обработки входящих веб-хуков"
                )
            elif webhook_server.get("status") == "issues":
                checks = webhook_server.get("checks", {})
                
                if not checks.get("fastapi_import", True):
                    recommendations.append(
                        "Добавьте импорт FastAPI в файл webhook_server.py"
                    )
                
                if not checks.get("error_handling", True):
                    recommendations.append(
                        "Добавьте обработку ошибок в webhook_server.py с использованием try-except и HTTPException"
                    )
                    
                if not checks.get("logging", True):
                    recommendations.append(
                        "Добавьте логирование в webhook_server.py для отладки проблем"
                    )
        
        # Проверка тестирования эндпоинтов
        if "endpoints" in results:
            endpoints = results["endpoints"]
            
            # Проверка health эндпоинта
            health = endpoints.get("health", {})
            if health.get("error"):
                recommendations.append(
                    "Невозможно подключиться к /health эндпоинту. Убедитесь, что веб-сервер запущен."
                )
            elif health.get("status") not in (200, 201, 202):
                recommendations.append(
                    f"Health эндпоинт вернул статус {health.get('status')}. Должен возвращать 200 OK."
                )
                
            # Проверка webhook эндпоинта
            webhook_head = endpoints.get("webhook_head", {})
            if webhook_head.get("error"):
                recommendations.append(
                    "Невозможно подключиться к /okdesk-webhook эндпоинту. Убедитесь, что маршрут определен."
                )
        
        # Проверка Docker
        if "docker" in results:
            docker = results["docker"]
            
            # Проверка docker-compose
            docker_compose = docker.get("docker_compose", {})
            if docker_compose.get("error"):
                recommendations.append(
                    "Создайте docker-compose.yml файл для деплоя приложения"
                )
            else:
                if not docker_compose.get("has_app", True):
                    recommendations.append(
                        "Добавьте сервис 'app' в docker-compose файл"
                    )
                
                if not docker_compose.get("has_nginx", True):
                    recommendations.append(
                        "Добавьте сервис 'nginx' в docker-compose файл для проксирования запросов"
                    )
                    
                if not docker_compose.get("has_ports", True):
                    recommendations.append(
                        "Определите порты в docker-compose файле для доступа к сервисам"
                    )
            
            # Проверка Dockerfile
            dockerfile = docker.get("dockerfile", {})
            if dockerfile.get("error"):
                recommendations.append(
                    "Создайте Dockerfile для контейнеризации приложения"
                )
            else:
                if not dockerfile.get("has_expose", True):
                    recommendations.append(
                        "Добавьте инструкцию EXPOSE в Dockerfile для указания порта"
                    )
        
        return recommendations

    def run_all_checks(self) -> Dict[str, Any]:
        """
        Запуск всех проверок
        
        Returns:
            Dict[str, Any]: Результаты всех проверок и рекомендации
        """
        print("\n🚀 Запуск всех проверок веб-хука...")
        
        results = {}
        
        # Проверка конфигурации
        results["config"] = self.check_config()
        
        # Проверка файла webhook_server.py
        results["webhook_server"] = self.check_webhook_server()
        
        # Проверка настройки Docker
        results["docker"] = self.check_docker_setup()
        
        # Тестирование эндпоинтов (только если указан base_url)
        if self.base_url and self.base_url != "http://localhost:8000":
            results["endpoints"] = self.test_webhook_endpoints()
        else:
            print("\n⚠️ Тестирование эндпоинтов пропущено (не указан URL)")
        
        # Генерация рекомендаций
        recommendations = self.generate_recommendations(results)
        results["recommendations"] = recommendations
        
        print("\n📋 Рекомендации:")
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
        else:
            print("✅ Нет рекомендаций, веб-хук настроен корректно!")
        
        return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Проверка и исправление проблем с веб-хуком")
    parser.add_argument("--url", type=str, help="URL для проверки веб-хука (например, http://example.com)")
    args = parser.parse_args()
    
    print("🔍 Анализ веб-хука")
    print("=" * 50)
    
    analyzer = WebhookAnalyzer(args.url)
    results = analyzer.run_all_checks()
    
    print("\n✅ Анализ завершен")
