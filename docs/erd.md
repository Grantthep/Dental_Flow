# DentalFlow — Database ERD (draft)

PostgreSQL. All timestamps are `timestamptz` (UTC). GitHub renders the diagram below.

```mermaid
erDiagram
    users ||--o| dentists : "may be"
    users ||--o{ audit_logs : "performs"
    users ||--o{ appointments : "created_by"
    dentists ||--o{ availability : "works"
    dentists ||--o{ time_off : "takes"
    dentists ||--o{ appointments : "treats"
    patients ||--o{ appointments : "books"

    users {
        int id PK
        string email UK
        string password_hash
        string full_name
        enum role "admin | receptionist | dentist"
        bool is_active
        timestamptz created_at
    }
    dentists {
        int id PK
        int user_id FK,UK "nullable"
        string full_name
        string specialty
        string phone
        string email
        bool is_active
        timestamptz created_at
    }
    patients {
        int id PK
        string first_name
        string last_name
        date date_of_birth
        string gender
        string phone
        string email
        string address
        text medical_notes
        bool is_active
        timestamptz created_at
        timestamptz updated_at
    }
    availability {
        int id PK
        int dentist_id FK
        smallint day_of_week "0=Mon .. 6=Sun"
        time start_time
        time end_time
    }
    time_off {
        int id PK
        int dentist_id FK
        timestamptz start_at
        timestamptz end_at
        string reason
    }
    appointments {
        int id PK
        int patient_id FK
        int dentist_id FK
        int created_by FK "users.id"
        timestamptz start_at
        timestamptz end_at
        enum status "booked | confirmed | completed | cancelled | no_show"
        string reason
        text notes
        timestamptz created_at
        timestamptz updated_at
    }
    audit_logs {
        int id PK
        int user_id FK
        string action "create | update | cancel | ..."
        string entity_type "appointment | patient | ..."
        int entity_id
        jsonb changes "before / after"
        timestamptz created_at
    }
```

## Key constraints
| Table | Constraint | Why |
|---|---|---|
| appointments | `CHECK (end_at > start_at)` | no zero/negative length |
| appointments | `EXCLUDE USING gist (dentist_id WITH =, tstzrange(start_at, end_at) WITH &&) WHERE (status NOT IN ('cancelled','no_show'))` | **double-booking prevention in the DB** (needs `btree_gist` extension) |
| availability | `CHECK (end_time > start_time)`, `CHECK (day_of_week BETWEEN 0 AND 6)` | valid blocks |
| time_off | `CHECK (end_at > start_at)` | valid period |
| users | `UNIQUE (email)` | login |
| dentists | `UNIQUE (user_id)` | one account per dentist |

## Indexes (initial)
- `appointments (dentist_id, start_at)` — calendar by dentist/date
- `appointments (patient_id, start_at)` — patient history
- `patients (last_name, first_name)`, `patients (phone)` — search
- `availability (dentist_id, day_of_week)`
- `audit_logs (entity_type, entity_id)`

## Notes
- Breaks are modelled as gaps between `availability` rows on the same day — no separate table.
- Nothing is hard-deleted except availability rows; patients/dentists use `is_active`.
