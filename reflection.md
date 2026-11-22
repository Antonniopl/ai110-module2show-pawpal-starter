# PawPal+ Project Reflection

## 1. System Design

### a. Initial design
An owner should be able to add a pet, schedule a care task for that pet, and see what needs doing today across all pets. `Owner` knows which pets belong to the household. `Pet` keeps its own list. A `Task` is one occurrence, not the entire recurring routine. `Scheduler` reads the household and prepares a view without making a second master list.
