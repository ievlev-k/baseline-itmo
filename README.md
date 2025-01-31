# FastAPI Baseline Service
Это пример базового приложения, которое реализует API для получения запроса и возврата ответа.
Приложение написано на FastAPI, разворачивается при помощи docker-compose.

## Сборка
Для запуска выполните команду:

```bash
docker-compose up -d
```
После чего необходимо выполнить комманды chmod +x end.sh
```bash
chmod +x end.sh
./end.sh
```
Это действие необходимо для отправки модели контейнер

Описание проблемы можно увидеть в https://stackoverflow.com/questions/77830020/how-to-compose-ollama-server-with-nextjs

Если кратко, то при запуске модели, compose не может найти команду ollama

