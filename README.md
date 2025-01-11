# Telegram Bot SLA

## Description

Telegram Bot SLA is a tool designed to simplify interactions between clients and support teams and automate request processing in chats. The bot helps comply with SLA (Service Level Agreement), notifies about response time breaches, and provides activity reports for team members.

---

## Main Features

1. **Task Creation**
   - The bot automatically creates tasks when clients send messages in chats.
   - If a client's message remains unanswered, the bot tracks the time until SLA violation.

2. **Task Closure**
   - If a support team member or admin replies to a client, the task is automatically closed.
   - Tasks can also be manually closed using the `/close` command.

3. **Notifications**
   - The bot sends notifications as SLA deadlines approach.
   - Notifications are sent 15, 10, and 5 minutes before an SLA breach.

4. **Role Management**
   - Admins can add/remove users from roles:
     - `support` – support team members.
     - `admin` – administrators.
     - `sales` – sales team members.
   - Management commands:
     - `/add_staff` – add a support team member.
     - `/remove_staff` – remove a support team member.
     - `/add_admin` – add an administrator.
     - `/remove_admin` – remove an administrator.
     - `/add_sales` – add a sales team member.
     - `/remove_sales` – remove a sales team member.

5. **Reports**
   - Weekly activity report:
     - Support team member activity statistics.
     - Number of SLA violations.
   - The report is automatically sent to a designated chat on schedule.

6. **Working Hours**
   - The bot operates during working hours only (07:00–23:00 on weekdays, 10:00–19:00 on weekends).
   - Notifications and task processing occur only within these hours.

7. **Database Integration**
   - PostgreSQL is used to store information about tasks, roles, and activity logs.

---

## Commands

| Command           | Description                                                   |
|--------------------|---------------------------------------------------------------|
| `/start`           | Welcome message with information about your role.            |
| `/add_staff`       | Add a support team member (requires `admin` role).           |
| `/remove_staff`    | Remove a support team member (requires `admin` role).        |
| `/add_admin`       | Add an administrator (requires `admin` role).               |
| `/remove_admin`    | Remove an administrator (requires `admin` role).            |
| `/add_sales`       | Add a sales team member (requires `admin` role).            |
| `/remove_sales`    | Remove a sales team member (requires `admin` role).         |
| `/check_roles`     | Check your current role.                                     |
| `/close`           | Close a task manually by specifying the chat title.          |

---

## Technical Details

1. **Database Integration**
   - PostgreSQL stores:
     - `staff` table for role management.
     - `tasks` table for task tracking.
     - `support_activity` table for collecting activity statistics.

2. **Docker**
   - The project is containerized using Docker and Docker Compose.
   - Containers:
     - `bot` – main bot logic.
     - `db` – PostgreSQL database.

3. **Data Encryption**
   - Encryption is used for security, covering keys and tokens.

4. **Working Hours**
   - Tasks are created and processed only during working hours.
   - Tasks created outside working hours will be processed on the next working day.

5. **Notifications**
   - SLA notifications are sent to a designated chat.

---

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/MihaRS2/TG_Bot_SLA.git
   cd TG_Bot_SLA
   ```

2. **Create `.env` File**
   Create a `.env` file in the project root with the following parameters:
   ```env
   BOT_TOKEN=your_bot_token
   DB_USER=postgres
   DB_PASSWORD=your_database_password
   DB_NAME=telegram_bot_db
   DB_HOST=db
   DB_PORT=5432
   ENCRYPTION_KEY=your_encryption_key
   NOTIFICATION_GROUP_ID=your_notification_group_id
   ```

3. **Run Docker Compose**
   Ensure Docker and Docker Compose are installed:
   ```bash
   docker-compose up -d
   ```

4. **Generate Encryption Keys**
   Run the `generate_key.py` script to generate an encryption key:
   ```bash
   python3 app/generate_key.py
   ```

5. **Encrypt Tokens**
   Use the `encrypt_data.py` and `encrypt_token.py` scripts to encrypt the bot token and other sensitive data.

---

## Usage

1. Add the bot to the chats where it will monitor client messages.
2. Set up user roles using the appropriate commands.
3. Monitor SLA notifications in the designated chat.
4. Receive weekly activity reports automatically.

---

## Limitations

- PostgreSQL is required for proper operation.
