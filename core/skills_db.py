"""Curated skill taxonomy.

Kept as plain Python (not JSON) so aliases can carry comments and stay easy to
extend. `CANONICAL` maps a lowercase alias -> the display name we show in the UI.
"""

SKILL_ALIASES: dict[str, list[str]] = {
    # --- Languages ---
    "Python": ["python", "python3", "py"],
    "R": ["r programming", "rlang"],
    "SQL": ["sql", "mysql", "postgresql", "postgres", "sqlite", "t-sql", "plsql"],
    "Java": ["java"],
    "JavaScript": ["javascript", "js", "es6"],
    "TypeScript": ["typescript", "ts"],
    "C++": ["c++", "cpp"],
    "Scala": ["scala"],
    "Go": ["golang"],
    # --- Data / ML ---
    "Machine Learning": ["machine learning", "ml", "supervised learning", "predictive modeling"],
    "Deep Learning": ["deep learning", "neural networks", "cnn", "rnn", "lstm", "transformers"],
    "NLP": ["nlp", "natural language processing", "text mining", "spacy", "nltk", "bert"],
    "Computer Vision": ["computer vision", "opencv", "image classification"],
    "Data Analysis": ["data analysis", "data analytics", "exploratory data analysis", "eda"],
    "Statistics": ["statistics", "statistical analysis", "hypothesis testing", "a/b testing", "regression"],
    "Data Visualization": ["data visualization", "matplotlib", "seaborn", "plotly", "tableau", "power bi", "looker"],
    "Feature Engineering": ["feature engineering", "feature selection"],
    "MLOps": ["mlops", "model deployment", "mlflow", "model monitoring"],
    "Time Series": ["time series", "forecasting", "arima", "prophet"],
    "Recommender Systems": ["recommender systems", "recommendation engine", "collaborative filtering"],
    # --- Libraries / frameworks ---
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "TensorFlow": ["tensorflow", "keras"],
    "PyTorch": ["pytorch", "torch"],
    "Streamlit": ["streamlit"],
    "Flask": ["flask"],
    "FastAPI": ["fastapi"],
    "Django": ["django"],
    "React": ["react", "react.js", "reactjs"],
    "Spark": ["spark", "pyspark", "apache spark"],
    "Airflow": ["airflow", "apache airflow"],
    # --- Cloud / infra ---
    "AWS": ["aws", "amazon web services", "ec2", "s3", "sagemaker", "lambda"],
    "Azure": ["azure", "microsoft azure"],
    "GCP": ["gcp", "google cloud", "bigquery", "vertex ai"],
    "Docker": ["docker", "containerization"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Git": ["git", "github", "gitlab", "version control"],
    "CI/CD": ["ci/cd", "continuous integration", "jenkins", "github actions"],
    "Linux": ["linux", "bash", "shell scripting"],
    # --- Data engineering ---
    "ETL": ["etl", "elt", "data pipelines", "data pipeline"],
    "Data Warehousing": ["data warehouse", "data warehousing", "snowflake", "redshift"],
    "MongoDB": ["mongodb", "nosql"],
    "Excel": ["excel", "advanced excel", "vlookup", "pivot tables"],
    # --- Soft / process ---
    "Problem Solving": ["problem solving", "analytical thinking", "critical thinking"],
    "Communication": ["communication", "stakeholder management", "presentation skills"],
    "Agile": ["agile", "scrum", "kanban", "jira"],
    "Leadership": ["leadership", "team lead", "mentoring"],
}

# alias -> canonical display name
CANONICAL: dict[str, str] = {
    alias: name for name, aliases in SKILL_ALIASES.items() for alias in aliases
}
# make sure the canonical name itself is always matchable
for _name in SKILL_ALIASES:
    CANONICAL.setdefault(_name.lower(), _name)

ALL_ALIASES: list[str] = sorted(CANONICAL.keys(), key=len, reverse=True)

# Using a tool is evidence for the underlying skill, even if the resume never
# names it. Value = how much credit the implied skill earns (0-1).
IMPLIES: dict[str, dict[str, float]] = {
    "scikit-learn": {"Machine Learning": 0.8, "Python": 0.5},
    "TensorFlow": {"Deep Learning": 0.85, "Machine Learning": 0.7, "Python": 0.5},
    "PyTorch": {"Deep Learning": 0.85, "Machine Learning": 0.7, "Python": 0.5},
    "NLP": {"Machine Learning": 0.5},
    "Computer Vision": {"Deep Learning": 0.6, "Machine Learning": 0.6},
    "Pandas": {"Data Analysis": 0.7, "Python": 0.6},
    "NumPy": {"Python": 0.6},
    "Data Visualization": {"Data Analysis": 0.5},
    "Time Series": {"Statistics": 0.6, "Machine Learning": 0.5},
    "Recommender Systems": {"Machine Learning": 0.7},
    "Spark": {"ETL": 0.6},
    "Airflow": {"ETL": 0.7},
    "Kubernetes": {"Docker": 0.7},
    "MLOps": {"Docker": 0.5, "CI/CD": 0.5},
    "Data Warehousing": {"SQL": 0.6, "ETL": 0.5},
    "Streamlit": {"Python": 0.5},
    "Flask": {"Python": 0.5},
    "FastAPI": {"Python": 0.5},
}

# Skills that carry more weight when a job description asks for them.
CORE_TECHNICAL = {
    "Python", "SQL", "Machine Learning", "Deep Learning", "NLP", "Data Analysis",
    "Statistics", "AWS", "GCP", "Azure", "Spark", "PyTorch", "TensorFlow",
    "scikit-learn", "Docker", "ETL",
}
