# Setup Instructions for Business Management Application

## **Quick Start with .env**

### **1. Clone the Repository**
```bash
git clone [your-repo-url]
cd [your-project-folder]
```

### **2. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **3. Configure Environment Variables**
Copy the `.env.example` file to `.env` and update with your settings:

```bash
cp .env.example .env
```

### **4. Edit .env File**
Open `.env` and update these values:
```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=gestion_negocio
DB_USER=your_username
DB_PASSWORD=your_password

# Application Configuration
APP_SECRET_KEY=your-very-secure-secret-key
APP_DEBUG=True
ENVIRONMENT=development
```

### **5. Run the Application**
```bash
python app.py
```

## **Environment Variables Reference**

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `3306` |
| `DB_NAME` | Database name | `gestion_negocio` |
| `DB_USER` | Database username | `pp` |
| `DB_PASSWORD` | Database password | `1234` |
| `APP_SECRET_KEY` | Application secret key | `dev-secret-key` |
| `APP_DEBUG` | Debug mode | `True` |
| `ENVIRONMENT` | Environment type | `development` |

## **Production Setup**
For production, create a `.env.production` file:
```bash
APP_DEBUG=False
ENVIRONMENT=production
APP_SECRET_KEY=your-production-secret-key
```

## **GitHub Integration**
The `.env` file is automatically ignored by git, so your sensitive data won't be uploaded to GitHub.
