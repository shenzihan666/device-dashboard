import { useState, useEffect, useCallback } from 'react';
import {
  getAppSettings,
  updateAppSettings,
  type AppSettingsState,
} from '../services/api';

const DEFAULTS: AppSettingsState = {
  point_to_point_enabled: true,
};

export function useAppSettings() {
  const [settings, setSettings] = useState<AppSettingsState>(DEFAULTS);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getAppSettings()
      .then((s) => {
        if (!cancelled) setSettings(s);
      })
      .catch(() => {
        /* keep defaults on error */
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const update = useCallback(async (patch: Partial<AppSettingsState>) => {
    const prev = settings;
    // optimistic
    setSettings((s) => ({ ...s, ...patch }));
    try {
      const next = await updateAppSettings(patch);
      setSettings(next);
    } catch {
      setSettings(prev);
    }
  }, [settings]);

  return { settings, loading, update };
}
