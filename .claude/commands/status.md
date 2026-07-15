# Status

Update the status of a work item.

Input: a work item key and a new status — e.g. "/status ST-002 in-progress".
Valid statuses ONLY: backlog | ready | in-progress | in-review | done.

Steps:
1. Find state/<...>.yaml matching the key. If no match, say so and stop.
2. Validate the requested status against the allowed set. If invalid, list the valid
   options and stop — do not write.
3. Update the `status` field to the new value and set `updated` to today's date.
4. Confirm: show the key, name, old status -> new status.

Rules:
- Only the `status` and `updated` fields change. Do not touch anything else.
- Reject invalid statuses rather than guessing the closest one.
- If no status is given (just a key), report the item's current status instead of changing it.
