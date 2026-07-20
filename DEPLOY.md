# Инструкция деплоя на сервер 167.71.63.195

## Шаг 1: Создать SSH-ключ на локальной машине (ПК)

Откройте PowerShell и выполните:

```powershell
ssh-keygen -t ed25519 -f $env:USERPROFILE\.ssh\id_ed25519 -N ""
```

Это создаст два файла:
- `~/.ssh/id_ed25519` (приватный ключ — НЕ делиться!)
- `~/.ssh/id_ed25519.pub` (публичный ключ — этот отправить на сервер)

## Шаг 2: Скопировать публичный ключ на сервер

Содержимое `~/.ssh/id_ed25519.pub` скопируйте и добавьте на сервер в файл `~/.ssh/authorized_keys`.

На сервере выполните:

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
cat >> ~/.ssh/authorized_keys << 'EOF'
# вставьте содержимое id_ed25519.pub сюда
EOF
chmod 600 ~/.ssh/authorized_keys
```

## Шаг 3: Проверить подключение

```powershell
ssh root@167.71.63.195
```

Если подключилось без пароля — всё готово!

## Шаг 4: Синхронизировать бот на сервере

На сервере перейдите в папку с ботом и выполните:

```bash
cd /path/to/bot
git pull origin stable
```

Если бот запущен через systemd/supervisor, перезагрузите его:

```bash
systemctl restart zosd_bot
# или
supervisorctl restart zosd_bot
```

## Примечание

После этого вы сможете синхронизировать через SSH без пароля:

```powershell
# с локального ПК:
ssh root@167.71.63.195 "cd /path/to/bot && git pull origin stable"
```
