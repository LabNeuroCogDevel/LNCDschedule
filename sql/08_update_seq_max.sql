SELECT setval('person_pid_seq', COALESCE((SELECT MAX(pid)+1 FROM person), 1), false);
