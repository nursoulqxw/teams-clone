# Teams Clone

A full-stack replica of a team collaboration platform inspired by Microsoft Teams. This project includes both backend and frontend components, allowing teams to collaborate via channels, messages, and team memberships.

---

## Table of Contents
- [Features](#features)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Setup Instructions](#setup-instructions)
  - [System Requirements](#system-requirements)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Contributing](#contributing)
- [License](#license)

---

## Features

### Backend:
- **Authentication & Authorization**: Custom user models with JWT-based authentication
- **Teams and Memberships**: Create, update, and manage teams and members
- **Channels**: Public and private channels for discussions
- **Messages**: Real-time message posting CRUD

### Frontend:
- **React-based UI** with routing and state management
- **Real-time updates and search**
- **Responsive design**

---

## Project Structure

```
teams-clone/
├── backend/
│   ├── apps/
│   │   ├── users/
│   │   ├── teams/
│   │   ├── channels/
│   │   └── messages/
│   ├── settings/
│   │   ├── base.py
│   │   ├── local.py
│   │   ├── prod.py
│   └── requirements/
│       ├── base.txt
│       ├── dev.txt
│       └── prod.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── api/
│   │   ├── types/
│   │   └── App.tsx
│   ├── public/
│   └── package.json
│
```

---

## Tech Stack
- **Backend**: Django, Django REST Framework
- **Frontend**: React, TypeScript
- **Database**: PostgreSQL

---

## Setup Instructions

### System Requirements

- **Backend**:
  - Python 3.8 or higher
  - PostgreSQL
- **Frontend**:
  - Node.js 16 or higher
  - npm or yarn

---

### Backend Setup

1. **Clone the Repository**
   ```shell
   git clone https://github.com/Nurasyl555/teams-clone.git
   cd teams-clone
   ```

2. **Configure Environment**
   - Navigate to the `backend/` directory.
   - Create an `.env` file by copying `.env.example`:
     ```shell
     cp .env.example .env
     ```
   - Update the `.env` file with your PostgreSQL credentials.

3. **Install Dependencies**
   ```shell
   pip install -r requirements/dev.txt
   ```

4. **Apply Migrations**
   ```shell
   python manage.py migrate
   ```

5. **Seed the Database**
   Run management commands to populate data:
   ```shell
   python manage.py seed_users
   python manage.py seed_teams
   python manage.py seed_channels
   python manage.py seed_messages
   ```

6. **Run the Development Server**
   ```shell
   python manage.py runserver
   ```

7. **Verify Endpoints**
   Test the APIs using tools like Postman.

---

### Frontend Setup

1. **Navigate to Frontend Directory**
   ```shell
   cd ../frontend
   ```

2. **Install Dependencies**
   Using npm:
   ```shell
   npm install
   ```

   Or with yarn:
   ```shell
   yarn install
   ```

3. **Start the Development Server**
   ```shell
   npm start
   ```
   The server will be available at `http://localhost:3000`.

4. **Build for Production**
   To create a production build, run:
   ```shell
   npm run build
   ```

---

## Contributing

1. Create a feature branch:
   ```shell
   git checkout -b feature/your-feature-name
   ```

2. Make changes and commit:
   ```shell
   git commit -m "Add your message here"
   ```

3. Push to the branch:
   ```shell
   git push origin feature/your-feature-name
   ```

4. Open a pull request on GitHub.

---

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

---

**Created by [Nurasyl555](https://github.com/Nurasyl555).**
