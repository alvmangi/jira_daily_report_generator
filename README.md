# Jira Daily Report Generator

This script generates a daily report of Jira tickets and sends it to a specified Slack channel. It's designed to help teams keep track of their daily progress and upcoming tasks.

## Features

- Retrieves Jira tickets assigned to the current user
- Filters tickets based on recent activity (last 24 hours, or last 3 days if it's Monday)
- Categorizes tickets into "What I did yesterday", "What I am doing today", and "Blocked tickets"
- Includes a random lunch suggestion
- Sends a formatted report to a specified Slack channel

## How it works

1. The script connects to Jira using the provided credentials
2. It retrieves tickets that the user has worked on recently
3. It categorizes these tickets based on their status
4. It generates a random lunch suggestion
5. It formats all this information into a Slack message
6. Finally, it sends the formatted message to the specified Slack channel

## Requirements

- Python 3.6+
- `requests` library
- `slack_sdk` library
- `python-dotenv` library
- Jira account with API access
- Slack bot token with permission to post messages

## Configuration

Before running the script, you need to set up the following environment variables:

- `JIRA_BASE_URL`: Your Jira instance URL
- `JIRA_USERNAME`: Your Jira username
- `JIRA_API_TOKEN`: Your Jira API token
- `SLACK_BOT_TOKEN`: Your Slack bot token
- `SLACK_CHANNEL_ID`: The ID of the Slack channel where the report will be posted

## Usage

Run the script daily to generate and send the report. In Linux/Unix systems, you can use cronjobs for this.


---

# Generador de Informes Diarios de Jira

Este script genera un informe diario de tickets de Jira y lo envía a un canal de Slack específico. Está diseñado para ayudar a los equipos a realizar un seguimiento de su progreso diario y de las tareas próximas.

## Características

- Recupera tickets de Jira asignados al usuario actual
- Filtra los tickets basándose en la actividad reciente (últimas 24 horas, o últimos 3 días si es lunes)
- Categoriza los tickets en "Lo que hice ayer", "Lo que estoy haciendo hoy" y "Tickets bloqueados"
- Incluye una sugerencia aleatoria para el almuerzo
- Envía un informe formateado a un canal de Slack específico

## Cómo funciona

1. El script se conecta a Jira utilizando las credenciales proporcionadas
2. Recupera los tickets en los que el usuario ha trabajado recientemente
3. Categoriza estos tickets basándose en su estado
4. Genera una sugerencia aleatoria para el almuerzo
5. Formatea toda esta información en un mensaje de Slack
6. Finalmente, envía el mensaje formateado al canal de Slack especificado

## Requisitos

- Python 3.6+
- Biblioteca `requests`
- Biblioteca `slack_sdk`
- Biblioteaca `python-dotenv`
- Cuenta de Jira con acceso a la API
- Token de bot de Slack con permiso para publicar mensajes

## Configuración

Antes de ejecutar el script, necesitas configurar las siguientes variables de entorno:

- `JIRA_BASE_URL`: La URL de tu instancia de Jira
- `JIRA_USERNAME`: Tu nombre de usuario de Jira
- `JIRA_API_TOKEN`: Tu token de API de Jira
- `SLACK_BOT_TOKEN`: Tu token de bot de Slack
- `SLACK_CHANNEL_ID`: El ID del canal de Slack donde se publicará el informe

## Uso

Ejecuta el script diariamente para generar y enviar el informe. Puedes usar un cronjob para esto en sistemas Linux/Unix.

