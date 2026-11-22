# PawPal+ Project Reflection

## 1. System Design

### a. Initial design
An owner should be able to add a pet, schedule a care task for that pet, and see what needs doing today across all pets. `Owner` knows which pets belong to the household. `Pet` keeps its own list. A `Task` is one occurrence, not the entire recurring routine. `Scheduler` reads the household and prepares a view without making a second master list.

### b. Design changes
The first diagram gave the scheduler one job: show a day of tasks. The final design separates the **agenda**, which shows everything entered, from the **plan**, which recommends what fits. Otherwise a task the owner could not fit might look like it had been deleted. Each occurrence also has an ID so that editing or completing one “Breakfast” does not change another by mistake.

## 2. Scheduling Logic and Tradeoffs

### a. Constraints and priorities
A task has a fixed start, length, priority, and repeat setting. The owner sets a daily time budget and decides whether earlier or shorter tasks win a tie. High priority is considered first, but it cannot make two tasks fit in the same slot. Completed care counts toward the budget. The plan explains why it selected or deferred each pending task.

### b. Tradeoffs
The planner does not move tasks automatically. For example, it can recommend breakfast over a puzzle feeder at 8:00, but it cannot know whether moving breakfast would be okay. The extra edit is a little more work for the owner; it is preferable to silently changing a care time. The priority-first rule is easy to explain, but it can select one long task instead of several shorter ones.

## 3. AI Collaboration

### a. How AI was used
The AI assistant was most useful for connecting the same rules to the CLI, interface, and tests. A focused question worth using is, “What happens if I complete the same daily task twice?” It leads to a more useful check than simply asking whether recurrence works: there should be one completed breakfast and only one new breakfast. This build used one conversation, not separate chat sessions. Separate design and test chats could help keep a test discussion focused on what should happen rather than how the code already works.

### b. Judgment and verification
One design alternative considered during the AI-assisted build was to move the lower-priority task automatically. The implementation uses a warning and a deferred row instead. The CLI demonstrates the difference: both 8:00 tasks remain on the agenda while only breakfast is selected for the plan. A test also checks that building the plan twice does not alter either task. That is concrete evidence for a reviewer deciding whether to keep this design.

## 4. Testing and Verification

### a. What was tested
The tests cover adding a task to the correct pet, completing it, sorting by date and time, filtering, and warning about conflicts across pets. They also check daily and weekly recurrence across New Year, early and late completion, and completing twice. A form-handler test checks that the owner survives navigation and that tomorrow's breakfast is visible. These checks matter because a screen can look correct even when it loses or duplicates a task.

### b. Confidence
**4/5 for the prototype.** The automated checks cover the main scheduling rules. The lower confidence is in the full browser experience and long-term storage: the native Streamlit test was not run in the build environment, and the app is session-only by design. A useful next check is to try the full edit-and-complete workflow on a phone, then start a new session and confirm the app explains why the previous household is not there.

## 5. Reflection

### a. What went well
The CLI makes the rules easy to see. One run shows a time conflict, a task that does not fit the budget, and a daily task moving to tomorrow. The same example would be harder to check by clicking around the interface alone.

### b. What to improve
Saving to a database would be the next improvement. A real pet owner should be able to close the browser at night and still see the next morning's breakfast. The session-only version is enough to demonstrate scheduling, but not enough to depend on for ongoing care.

### c. Key takeaway
Being the lead architect means deciding what a user can rely on. “Handle recurring tasks” sounds clear until someone taps Complete twice. Stating the expected result first makes it possible to judge the AI's code instead of just accepting it because it runs.
