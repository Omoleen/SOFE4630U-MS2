import redis        # pip install redis
import io;
import base64

ip="34.130.127.228"
r = redis.Redis(host=ip, port=6379, db=0,password='sofe4630u')

value=r.get('image');
decoded_value=base64.b64decode(value);

with open("./received.jpg", "wb") as f:
    f.write(decoded_value);
    
print('Image received, check ./received.jpg')
