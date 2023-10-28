from datetime import datetime, timedelta

now = datetime.now()
then =datetime.now() + timedelta(hours =100)

print((then-now)- timedelta(hours = 12))