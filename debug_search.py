
try:
    from api.admin_utils import search_untappd_venues
    print("Import successful")
    results = search_untappd_venues("mountain culture")
    print(f"Results type: {type(results)}")
    print(results)
except Exception as e:
    print(f"CRASHED: {e}")
    import traceback
    traceback.print_exc()
