# DentalFlow — Frontend: pages, wireframes and style

> Member 2 (Frontend). Next.js (App Router) + TypeScript + Tailwind CSS.

## Pages and navigation
| Path | Page | Who sees it |
|---|---|---|
| `/` | Dashboard — today's appointments, next patient, quick status actions | all |
| `/calendar` | Calendar — day view (one column per dentist) and week view | all |
| `/patients` | Patient search (name / phone), paginated, "New patient" | all (create: A R) |
| `/patients/[id]` | Patient detail, edit, deactivate, appointment history | all (edit: A R) |
| `/appointments/new` | Booking form: patient → dentist → date → free slot | A R |
| `/appointments/[id]` | Appointment detail: status, notes, reschedule, cancel | all (reschedule/cancel: A R) |
| `/reports` | Clinic analytics: rates, appointments over time, per dentist, CSV export | A |
| `/login` | Login — to be wired up with Member 3's auth API (not built yet) | all |

Navigation: fixed sidebar on desktop/tablet, collapsible menu on phones. Items the current role
can't use are hidden; pages also show a "no access" message if opened directly.

## Wireframes

### Layout shell
```
+--------------+---------------------------------------------------+
| 🦷 DentalFlow |  Page title                       [role ▾] [user] |
|              +---------------------------------------------------+
| Dashboard    |                                                   |
| Calendar     |                 page content                      |
| Patients     |                                                   |
| New booking  |                                                   |
| Reports      |                                                   |
+--------------+---------------------------------------------------+
```

### Login
```
            +-------------------------------+
            |        🦷 DentalFlow           |
            |  Email     [_______________]  |
            |  Password  [_______________]  |
            |  [          Sign in         ] |
            |  error message here           |
            +-------------------------------+
```

### Calendar (day view, one column per dentist)
```
[< ] [Today] [ >]  Mon 20 Oct 2026          [Day|Week]  Dentist [All ▾]  [ ] show cancelled
       | Dr. Aung        | Dr. Mya          | Dr. Zaw
 09:00 | ┌ 09:00 Su Su ┐ |                  |
 09:30 | └ Check-up    ┘ | ┌ 09:30 Ko Ko ┐  |
 10:00 |                 | └ Filling     ┘  |   (click empty space → book at that time)
 ...
```
Week view: one column per day (Mon–Sun), blocks show time, patient and dentist.

### Booking form
```
Patient   [search name/phone......]  (+ New patient)
          > Su Su Hlaing  09 123 456
Dentist   [Dr. Aung ▾]   Date [2026-10-20]   Length [30 min ▾]
Free slots [09:00] [09:15] [09:30] [10:30] ...
Reason    [______________]
Notes     [______________]
                                      [Cancel] [Book appointment]
⚠ Dentist already has an appointment at this time   (409 errors shown here)
```

### Patient search / detail
```
[Search name or phone_____]  [ ] include inactive     [+ New patient]
Name            Phone         Date of birth   Email
Hlaing, Su Su   09 123 456    1990-02-01      su@example.com
...                                   « Prev   page 1 of 3   Next »

Patient detail:  name, phone, DOB, email, address, medical notes
[Edit] [Book appointment] [Deactivate]
History: date | dentist | reason | status
```

### Dentist dashboard
```
Dentist [All ▾]
[Today 12] [Upcoming 7] [Completed 4] [No-show 1]
Next patient: 10:30 Ko Ko — Filling (Dr. Mya)          [Open]
Today's list: time | patient | dentist | reason | status | [Confirm][Done][No-show]
```

### Reports
```
From [date] To [date]  Group [Day ▾]  Dentist [All ▾]              [Export CSV]
[Appointments 230] [Completed 180] [Cancellation 6.1%] [No-show 3.4%]
Appointments over time   ▇▇▅▇▇▆ (stacked: completed / upcoming / cancelled / no-show)
Per dentist table: dentist | total | completed | cancelled | no-show | chair hours
```

## Style
- Clean, light clinical look: white cards on a slate-50 background, rounded corners, thin borders.
- Primary colour **teal-600** (buttons, active nav); text slate-900 / slate-600.
- Appointment status colours (always shown with the status text, never colour alone):
  booked = blue, confirmed = indigo, completed = green, cancelled = slate (struck through), no-show = amber.
- Times are shown in the clinic timezone (`NEXT_PUBLIC_CLINIC_TZ`, default `Asia/Yangon`), whatever the browser's timezone.
- Desktop and tablet first; phones get a collapsed menu.
