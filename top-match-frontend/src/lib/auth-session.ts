type SessionListener = () => void;

const listeners = new Set<SessionListener>();

export function subscribeSession(listener: SessionListener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function emitSessionChanged(): void {
  for (const listener of listeners) {
    listener();
  }
}
