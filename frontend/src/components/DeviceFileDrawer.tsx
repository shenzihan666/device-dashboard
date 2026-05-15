import { useState, useEffect } from 'react';
import { X, FileText, File, Database, FileSpreadsheet, HardDrive } from 'lucide-react';
import type { DeviceFileInfo } from '../services/api';
import { getDeviceFiles } from '../services/api';
import FileViewer from './FileViewer';

interface DeviceFileDrawerProps {
  deviceId: string;
  deviceName: string;
  onClose: () => void;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString('en-US', { hour12: false });
  } catch {
    return iso;
  }
}

function FileIcon({ extension }: { extension: string }) {
  switch (extension) {
    case '.log':
    case '.jsonl':
      return <FileText className="w-4 h-4 text-blue-500" />;
    case '.db':
      return <Database className="w-4 h-4 text-amber-500" />;
    case '.xlsx':
    case '.xls':
      return <FileSpreadsheet className="w-4 h-4 text-emerald-500" />;
    default:
      return <File className="w-4 h-4 text-gray-400" />;
  }
}

export default function DeviceFileDrawer({ deviceId, deviceName, onClose }: DeviceFileDrawerProps) {
  const [files, setFiles] = useState<DeviceFileInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<DeviceFileInfo | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getDeviceFiles(deviceId)
      .then((res) => setFiles(res.files))
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load files'))
      .finally(() => setLoading(false));
  }, [deviceId]);

  return (
    <div className="fixed top-0 right-0 w-[640px] h-full bg-white border-l border-gray-200 z-50 flex flex-col shadow-[0_8px_30px_rgba(0,0,0,0.06)] animate-slide-in">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex justify-between items-center">
        <div className="flex items-center gap-2 min-w-0">
          <HardDrive className="w-4 h-4 text-blue-500 shrink-0" />
          <h3 className="text-sm font-semibold text-gray-800 truncate">
            {selectedFile ? selectedFile.filename : `${deviceName} — Log Files`}
          </h3>
        </div>
        <button
          className="p-1 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
          onClick={onClose}
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Body */}
      {selectedFile ? (
        <FileViewer
          deviceId={deviceId}
          file={selectedFile}
          onBack={() => setSelectedFile(null)}
        />
      ) : (
        <div className="flex-1 overflow-y-auto">
          {loading && (
            <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
              Loading files...
            </div>
          )}
          {error && (
            <div className="p-4 text-red-500 text-sm">{error}</div>
          )}
          {!loading && !error && files.length === 0 && (
            <div className="flex flex-col items-center justify-center h-48 text-gray-400">
              <FileText className="w-8 h-8 mb-2" />
              <span className="text-sm">No log files found for this device</span>
            </div>
          )}
          {!loading && !error && files.length > 0 && (
            <div className="p-2">
              {files.map((file) => (
                <button
                  key={file.file_id}
                  onClick={() => setSelectedFile(file)}
                  className="w-full text-left p-3 rounded-lg hover:bg-gray-50 transition-colors flex items-start gap-3 group"
                >
                  <FileIcon extension={file.extension} />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-800 truncate group-hover:text-blue-600 transition-colors">
                      {file.filename}
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-[10px] text-gray-500">
                      <span>{formatSize(file.size)}</span>
                      <span>•</span>
                      <span>{formatDate(file.uploaded_at)}</span>
                      {file.upload_kind && (
                        <>
                          <span>•</span>
                          <span className="px-1.5 py-0.5 bg-gray-100 rounded">{file.upload_kind}</span>
                        </>
                      )}
                      {file.source_system && (
                        <span className="px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded">{file.source_system}</span>
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
