# Text a guest when their table is ready

<!-- An invented example of templates/feature-doc.md, filled in: a walk-in waitlist app for a restaurant.
Not a real project; every name, number and finding below is made up. -->

## 1. In short

When a table frees up, the host taps one button. The next guest on the waitlist then gets a text saying their table
is ready. Guests can wander off while they wait instead of standing at the door.

## 2. What you can do now

Open the waitlist screen and add a guest with a phone number. Then tap "Table ready" on their row. The row turns
green and shows "Texted 19:42". The guest's phone gets: "Your table is ready. Please come to the host stand within
10 minutes." To try it without sending a real text, start the app in demo mode:

`make demo`

Demo mode fills the list with five made-up guests. Their phone numbers are in the range set aside for films and
tests. So no real phone can ever receive one of these texts.

## 3. What it protects you from

- **Texting the wrong person.** The review found that two quick taps on "Table ready" could also text the next
  guest. That is fixed: a second tap within 5 seconds does nothing, and a test proves it.
- **Texting a real stranger from a test.** The automatic tests never send a real text. They use a stand-in for the
  text-message service. The app also refuses to start in demo mode with a live text-message account.
- **Silent failures.** If a text cannot be sent, the row turns red and says "Not sent - tell the guest in person".
  It never looks as if it worked.

## 4. Not done yet

- Guests cannot reply to the text yet, for example "running 5 minutes late". A later ticket adds that.
- The 10-minute wait in the message is fixed for now. The owner cannot change it from a settings screen yet.

---

## 5. For developers and coding agents

Ticket: M1-NOTIFY-02 · Archetype: none

### 5.1 Contract

- Consumes: `WaitlistEntry` (id, guest_name, phone_e164, status) from #Contracts.
- Exposes: `notify_table_ready(entry_id) -> NotifyResult` (sent | duplicate | failed, with `sent_at`).

### 5.2 Files

- `app/notify/service.py` - `notify_table_ready`, the duplicate guard (5-second window per entry) and the failure path.
- `app/notify/sms_adapter.py` - the only file that imports the text-message vendor's SDK.
- `app/notify/tests/test_notify.py` - 9 tests, the vendor behind a recording fake.
- `app/waitlist/routes.py` - the "Table ready" button's route, wired to `notify_table_ready`.
- `app/demo/seed.py` (not in the ticket) - demo guests now use the reserved +44 7700 900000-900999 range and
  "(fictional)" names; the old seed used random numbers that could be real.

### 5.3 How it was verified

- `make check` → `48 passed in 6.1s`; ruff clean; structure check clean.
- `python -m app.devserver check /waitlist` → the row shows "Texted"; the fake recorded one message to +447700900123.
- Live-path checks walked: route registered on the serving app · outside call behind an adapter.
- Real-world reach: a real guest's phone - guarded by test_demo_numbers_are_reserved and
  test_demo_refuses_live_sms_account.
- Generated data pin: test_demo_seed_hash (the five seeded rows hash to a fixed value).
- Step 3c: no contradiction with #Contracts, #Architecture, #Scope or DESIGN.md.

### 5.4 Review

code + security review R1 2 findings · R2 (1 file) 0 findings

| Severity | File:line | What goes wrong | Fixed by |
|---|---|---|---|
| MEDIUM | `app/notify/service.py:41` | a double tap texts the next guest too | duplicate guard + test_double_tap_sends_once |
| LOW | `app/notify/sms_adapter.py:18` | the vendor's error text was dropped from the log | logged with the entry id |

- `app/notify/service.py` - duplicate guard, failure path, no swallowed errors.
- `app/notify/sms_adapter.py` - the only vendor import; the key read from settings, never logged.
- `app/waitlist/routes.py` - the route checks the host is signed in to this restaurant.
- `app/demo/seed.py` - every phone number in the reserved range; names marked "(fictional)".
