install:
	rm -fr venv && virtualenv venv && pip install -r requirements.pip && . venv/bin/activate