/** Coalesces one rotating credential in a single Web process; never authorizes requests. */
export class SessionRefreshCoordinator<T extends { ok: boolean }> {
  private entries = new Map<string, { promise: Promise<T>; expiresAt: number }>();

  private readonly reuseMs: number;
  private readonly capacity: number;
  constructor(reuseMs = 5000, capacity = 256) {
    this.reuseMs = reuseMs;
    this.capacity = capacity;
  }

  run(key: string, refresh: () => Promise<T>): Promise<T> {
    const now = Date.now();
    for (const [storedKey, entry] of this.entries) {
      if (entry.expiresAt <= now) this.entries.delete(storedKey);
    }
    const existing = this.entries.get(key);
    if (existing) return existing.promise;
    if (this.entries.size >= this.capacity) return Promise.reject(new Error("Refresh coordinator busy"));

    // Register before calling refresh so concurrent route handlers share its promise.
    const entry = { promise: Promise.resolve().then(refresh), expiresAt: Infinity };
    this.entries.set(key, entry);
    entry.promise = entry.promise.then(result => {
      if (!result.ok) {
        this.entries.delete(key);
      } else {
        entry.expiresAt = Date.now() + this.reuseMs;
        setTimeout(() => {
          if (this.entries.get(key) === entry) this.entries.delete(key);
        }, this.reuseMs).unref();
      }
      return result;
    }, error => {
      this.entries.delete(key);
      throw error;
    });
    return entry.promise;
  }
}
