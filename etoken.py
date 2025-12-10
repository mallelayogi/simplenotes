from itsdangerous import URLSafeTimedSerializer
from config import secret_key,salt

#Encoding serilizer
def endata(data):
    serializer = URLSafeTimedSerializer(secret_key)
    return serializer.dumps(data,salt=salt)

#Decoding serilizer
def dcdata(data):
    serializer = URLSafeTimedSerializer(secret_key)
    return serializer.loads(data,salt=salt)