# Mermaid-Diagram for IBDb

Dette er et mermaid-diagram laget ved hjelp av Anthropics KI-modell *Claude*. Jeg planla originalt å tegne den selv, men fikk tekniske problemer med applikasjonen jeg valgte. Mermaid-diagrammet ser slik ut:

```mermaid
erDiagram
  role ||--o{ user : "has"
  user ||--o{ question : "asks"
  user }o--o{ boardgame : "favourites"

  role {
    int id PK
    varchar name
  }
  user {
    int id PK
    varchar username
    varchar email
    char password
    int role_id FK
    tinyint active
  }
  boardgame {
    int id PK
    varchar name
    int year_published
    varchar creator
    varchar publisher
    varchar img_filename
    text description
  }
  question {
    int id PK
    text question
    timestamp created_on
    int user_id FK
  }
```