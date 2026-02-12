import requests

images = [
    "https://images.unsplash.com/photo-1571613316887-6f8d5cbf7ef7?w=1200&q=80",
    "https://images.unsplash.com/photo-1575037614876-c38a4d44f5b8?w=1200&q=80",
    "https://images.unsplash.com/photo-1567696911980-2eed69a46042?w=1200&q=80",
    "https://images.unsplash.com/photo-1559526323-cb2f2fe2591b?w=1200&q=80",
    "https://images.unsplash.com/photo-1518176258769-f227c798150e?w=1200&q=80",
    "https://images.unsplash.com/photo-1436076863939-06870fe779c2?w=1200&q=80",
    "https://images.unsplash.com/photo-1584225064785-c62a8b43d148?w=1200&q=80",
    "https://images.unsplash.com/photo-1535958636474-b021ee8876a3?w=1200&q=80",
    "https://images.unsplash.com/photo-1572116469696-9a25f82d1c67?w=1200&q=80", 
    "https://images.unsplash.com/photo-1578507065211-1c4e99a5fd11?w=1200&q=80",
    "https://images.unsplash.com/photo-1600788886242-5c96aabe3757?w=1200&q=80" 
]

valid_images = []
for url in images:
    try:
        r = requests.head(url, timeout=5)
        if r.status_code == 200:
            print(f"OK: {url}")
            valid_images.append(url)
        else:
            print(f"FAIL ({r.status_code}): {url}")
    except Exception as e:
        print(f"ERROR: {url} - {e}")

print("\nValid List:")
print(valid_images)