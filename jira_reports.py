#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Alvaro Mantilla Gimenez (Alvis)

import os
from dotenv import load_dotenv
import requests
import logging
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Needed values
load_dotenv()

JIRA_BASE_URL = os.getenv('JIRA_BASE_URL')
JIRA_USERNAME = os.getenv('JIRA_USERNAME')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_CHANNEL_ID = os.getenv('SLACK_CHANNEL_ID')

# Slack's Client Initialization
slack_client = WebClient(token=SLACK_BOT_TOKEN)

# Ticket Class
class Ticket:
    def __init__(self, ticket_id, title, status, last_comment, url):
        self.id = ticket_id
        self.title = title
        self.status = status
        self.last_comment = last_comment
        self.url = url

    def format_for_slack(self):
        return [
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": "*Ticket ID*"},
                    {"type": "mrkdwn", "text": "*Status*"},
                    {"type": "mrkdwn", "text": f"<{self.url}|{self.id}>"},
                    {"type": "mrkdwn", "text": f"{self.status}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Title*: {self.title}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Last comment*: {self.last_comment[:100]}..." if len(self.last_comment) > 100 else f"*Last comment*: {self.last_comment}"
                }
            }
        ]

# Report Class
class Report:
    def __init__(self):
        self.previous_tickets = []
        self.next_tickets = []
        self.blocked_tickets = []
        self.lunch = None

    def add_previous_ticket(self, ticket):
        self.previous_tickets.append(ticket)

    def add_next_ticket(self, ticket):
        self.next_tickets.append(ticket)

    def add_blocked_ticket(self, ticket):
        self.blocked_tickets.append(ticket)

    def set_lunch(self, meal_name, recipe_url):
        self.lunch = (meal_name, recipe_url)

    def format_for_slack(self):
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":dart: *What I did yesterday?:*"
                }
            }
        ]

        for ticket in self.previous_tickets:
            blocks.extend(ticket.format_for_slack())

        blocks.extend([
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "\n\n:male-technologist: *What I am doing today?*"
                }
            }
        ])

        for ticket in self.next_tickets:
            blocks.extend(ticket.format_for_slack())

        if self.blocked_tickets:
            blocks.extend([
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "\n\n:octagonal_sign: *Tickets blocked?*"
                    }
                }
            ])
            for ticket in self.blocked_tickets:
                blocks.extend(ticket.format_for_slack())

        if self.lunch:
            meal_name, recipe_url = self.lunch
            blocks.extend([
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"\n\n:sandwich: *Lunch:*\nI would like for lunch :thinking_face:...{meal_name}.\n <{recipe_url}|Recipe>"
                    }
                }
            ])

        return blocks

    def __del__(self):
        print("Report object is being destroyed.")

# ReportFactory Class
class ReportFactory:
    @staticmethod
    def create_report():
        return Report()

# Get Jira tickets updated in the last 24 hours or 3 days if today is Monday
def get_jira_tickets():
    now = datetime.now()
    if now.weekday() == 0:  # Monday
        start_date = now - timedelta(days=3)  # Friday
    else:
        start_date = now - timedelta(days=1)

    jql_query = f'''
        assignee = currentUser()
        AND updated >= "{start_date.strftime("%Y-%m-%d")}"
        AND status in ("In Progress", "IN PROGRESS", "On Hold", "ON HOLD", "Blocked", "BLOCKED")
        ORDER BY updated DESC
    '''

    url = f"{JIRA_BASE_URL}/rest/api/2/search"
    auth = (JIRA_USERNAME, JIRA_API_TOKEN)
    headers = {"Accept": "application/json"}
    params = {
        "jql": jql_query,
        "fields": "key,status,comment,summary",
        "expand": "changelog"
    }

    try:
        response = requests.get(url, auth=auth, headers=headers, params=params)
        response.raise_for_status()
        issues = response.json()['issues']

        tickets = []
        for issue in issues:
            ticket_id = issue['key']
            title = issue['fields']['summary']
            status = issue['fields']['status']['name']

            # Verify if the user commented in the time window
            user_commented = False
            last_comment = None
            if 'comment' in issue['fields'] and issue['fields']['comment']['comments']:
                for comment in reversed(issue['fields']['comment']['comments']):
                    comment_date = datetime.strptime(comment['created'][:10], "%Y-%m-%d")
                    if comment_date >= start_date:
                        if comment['author'].get('name', comment['author'].get('displayName', '')) == JIRA_USERNAME:
                            user_commented = True
                            break
                    else:
                        break  # No need to review older comments

                # Get the last comment
                last_comment = issue['fields']['comment']['comments'][-1]['body']

            # If there is no comments from the user then verify the user worked previously on this ticket.
            if not user_commented:
                user_worked_on_ticket = False
                for history in issue['changelog']['histories']:
                    history_date = datetime.strptime(history['created'][:10], "%Y-%m-%d")
                    if history_date >= start_date:
                        author_name = history['author'].get('name', history['author'].get('displayName', ''))
                        if author_name == JIRA_USERNAME:
                            user_worked_on_ticket = True
                            break

                if not user_worked_on_ticket:
                    continue  # Skip this ticket if the user has not worked on it.

            last_comment_text = last_comment if last_comment else "No comments"
            ticket_url = f"{JIRA_BASE_URL}/browse/{ticket_id}"

            tickets.append(Ticket(ticket_id, title, status, last_comment_text, ticket_url))

        return tickets
    except requests.RequestException as e:
        logging.error(f"Error getting Jira tickets: {e}")
        return []

# Next work session tickets
def get_next_session_tickets():
    jql_query = 'assignee = currentUser() AND status in ("In Progress", "On Hold", "ON HOLD", "To Do", "TO DO") ORDER BY priority DESC, duedate ASC'
    url = f"{JIRA_BASE_URL}/rest/api/2/search"
    auth = (JIRA_USERNAME, JIRA_API_TOKEN)
    headers = {"Accept": "application/json"}
    params = {
        "jql": jql_query,
        "fields": "key,status,comment,summary"
    }

    try:
        response = requests.get(url, auth=auth, headers=headers, params=params)
        response.raise_for_status()
        issues = response.json()['issues']

        tickets = []
        for issue in issues:
            ticket_id = issue['key']
            title = issue['fields']['summary']
            status = issue['fields']['status']['name']
            last_comment = "No comments"
            if 'comment' in issue['fields'] and issue['fields']['comment']['comments']:
                last_comment = issue['fields']['comment']['comments'][-1]['body']
            ticket_url = f"{JIRA_BASE_URL}/browse/{ticket_id}"

            tickets.append(Ticket(ticket_id, title, status, last_comment, ticket_url))

        # Update ticket status if needed
        in_progress = [t for t in tickets if t.status == 'In Progress']
        on_hold = [t for t in tickets if t.status in ['On Hold', 'ON HOLD']]
        to_do = [t for t in tickets if t.status in ['To Do', 'TO DO']]

        while len(in_progress) < 3:
            if on_hold:
                ticket = on_hold.pop(0)
                if update_ticket_status(ticket.id, 'In Progress'):
                    ticket.status = 'In Progress'
                    in_progress.append(ticket)
            elif to_do:
                ticket = to_do.pop(0)
                if update_ticket_status(ticket.id, 'In Progress'):
                    ticket.status = 'In Progress'
                    in_progress.append(ticket)
            else:
                break

        return in_progress[:3]
    except requests.RequestException as e:
        logging.error(f"Error getting tickets for next work session: {e}")
        return []

# Blocked Tickets
def get_blocked_tickets():
    jql_query = 'assignee = currentUser() AND status in ("Blocked", "BLOCKED")'
    url = f"{JIRA_BASE_URL}/rest/api/2/search"
    auth = (JIRA_USERNAME, JIRA_API_TOKEN)
    headers = {"Accept": "application/json"}
    params = {
        "jql": jql_query,
        "fields": "key,status,comment,summary"
    }

    try:
        response = requests.get(url, auth=auth, headers=headers, params=params)
        response.raise_for_status()
        issues = response.json()['issues']

        tickets = []
        for issue in issues:
            ticket_id = issue['key']
            title = issue['fields']['summary']
            status = issue['fields']['status']['name']
            last_comment = "No comments"
            if 'comment' in issue['fields'] and issue['fields']['comment']['comments']:
                last_comment = issue['fields']['comment']['comments'][-1]['body']
            ticket_url = f"{JIRA_BASE_URL}/browse/{ticket_id}"

            tickets.append(Ticket(ticket_id, title, status, last_comment, ticket_url))

        return tickets
    except requests.RequestException as e:
        logging.error(f"Error al obtener tickets bloqueados: {e}")
        return []

# Update ticket status
def update_ticket_status(ticket_key, new_status):
    url = f"{JIRA_BASE_URL}/rest/api/2/issue/{ticket_key}/transitions"
    auth = (JIRA_USERNAME, JIRA_API_TOKEN)
    headers = {"Content-Type": "application/json"}

    try:
        # Get Jira transitions for the ticket
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        transitions = response.json()['transitions']

        # Get transition ID that matches the new status
        transition_id = next((t['id'] for t in transitions if t['to']['name'] == new_status), None)

        if transition_id is None:
            logging.error(f"There isn't a valid transtition for '{new_status}' in ticket {ticket_key}")
            return False

        # Transition Ticket to new status
        data = {
            "transition": {
                "id": transition_id
            }
        }
        response = requests.post(url, json=data, headers=headers, auth=auth)
        response.raise_for_status()

        logging.info(f"Ticket status for {ticket_key} has been updated to '{new_status}'")
        return True

    except requests.RequestException as e:
        logging.error(f"Error updating ticket status for {ticket_key}: {e}")
        return False

# Random recipe for lunch section
def get_random_recipe():
    try:
        '''
        This API is great. Kudos to the author/s.
        '''
        url = "https://www.themealdb.com/api/json/v1/1/random.php"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        meal = data['meals'][0]
        return meal['strMeal'], meal['strSource']
    except requests.RequestException as e:
        logging.error(f"Error geting random: {e}")
        return "Chef's Special", "No recipe available"

# Send to Slack
def send_to_slack(blocks):
    fallback_text = "Daily Jira Report"

    try:
        response = slack_client.chat_postMessage(
            channel=SLACK_CHANNEL_ID,
            blocks=blocks,
            text=fallback_text
        )
        logging.info("Slack message sent successfully.")
    except SlackApiError as e:
        logging.error(f"Error sending message to Slack: {e}")

# Main function
def main():
    logging.info("Initiating Jira's Report")

    report = ReportFactory.create_report()

    previous_tickets = get_jira_tickets()
    for ticket in previous_tickets:
        report.add_previous_ticket(ticket)

    next_tickets = get_next_session_tickets()
    for ticket in next_tickets:
        report.add_next_ticket(ticket)

    blocked_tickets = get_blocked_tickets()
    for ticket in blocked_tickets:
        report.add_blocked_ticket(ticket)

    meal_name, recipe_url = get_random_recipe()
    report.set_lunch(meal_name, recipe_url)

    blocks = report.format_for_slack()
    send_to_slack(blocks)

    logging.info("Report has been sent!")

    del report

# Script entry point.
if __name__ == "__main__":
    main()
