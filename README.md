# ContinuousGPT

ContinuousGPT generates insights into your conversation as it happens, helping you close that important sales call or discussing travel plans with your friend.

# Run
```
gunicorn -b :8000 --worker-class gevent app:app
```