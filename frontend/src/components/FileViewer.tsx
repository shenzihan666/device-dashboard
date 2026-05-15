import { useState, useEffect, useCallback } from 'react';
import { ArrowLeft, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Search } from 'lucide-react';
import type { DeviceFileInfo, FileContentResponse } from '../services/api';
import { getFileContent } from '../services/api';

const LINES_PER_PAGE = 500;

interface FileViewerProps {
  deviceId: string;
  file: DeviceFileInfo;
  onBack: () => void;
}

function formatNumber(n: number): string {
  return n.toLocaleString();
}

export default function FileViewer({ deviceId, file, onBack }: FileViewerProps) {
  const [content, setContent] = useState<FileContentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [jumpToLine, setJumpToLine] = useState('');

  const totalPages = content ? Math.ceil(content.total_lines / LINES_PER_PAGE) : 0;

  const fetchContent = useCallback(async (page: number) => {
    const offset = page * LINES_PER_PAGE;
    setLoading(true);
    setError(null);
    try {
      const res = await getFileContent(deviceId, file.file_id, offset, LINES_PER_PAGE);
      setContent(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load file content');
    } finally {
      setLoading(false);
    }
  }, [deviceId, file.file_id]);

  useEffect(() => {
    fetchContent(currentPage);
  }, [currentPage, fetchContent]);

  function goToPage(page: number) {
    if (page >= 0 && page < totalPages) {
      setCurrentPage(page);
    }
  }

  function handleJumpToLine() {
    const line = parseInt(jumpToLine, 10);
    if (isNaN(line) || line < 1) return;
    const page = Math.floor((line - 1) / LINES_PER_PAGE);
    setCurrentPage(page);
    setJumpToLine('');
  }

  const startLine = content ? content.offset + 1 : 0;
  const endLine = content ? content.offset + content.lines.length : 0;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center gap-2">
        <button
          onClick={onBack}
          className="p-1 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <span className="text-sm font-medium text-gray-800 truncate flex-1" title={file.filename}>
          {file.filename}
        </span>
        {content && (
          <span className="text-[10px] text-gray-500 shrink-0">
            {formatNumber(startLine)}-{formatNumber(endLine)} / {formatNumber(content.total_lines)} lines
          </span>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto bg-gray-50">
        {loading && !content && (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm">
            Loading...
          </div>
        )}
        {error && (
          <div className="p-4 text-red-500 text-sm">{error}</div>
        )}
        {content && content.lines.length === 0 && (
          <div className="p-4 text-gray-400 text-sm text-center">Empty file</div>
        )}
        {content && content.lines.length > 0 && (
          <div className="font-mono text-xs leading-5">
            {content.lines.map((line, i) => (
              <div key={i} className="flex hover:bg-blue-50">
                <span className="w-16 shrink-0 text-right pr-3 text-gray-400 select-none text-[10px] leading-5">
                  {content.offset + i + 1}
                </span>
                <span className="whitespace-pre text-gray-700 leading-5">{line}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 0 && (
        <div className="px-4 py-2 border-t border-gray-200 flex items-center gap-2 text-xs text-gray-600">
          <button
            onClick={() => goToPage(0)}
            disabled={currentPage === 0 || loading}
            className="p-1 rounded hover:bg-gray-100 disabled:opacity-30 transition-colors"
            title="First page"
          >
            <ChevronsLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => goToPage(currentPage - 1)}
            disabled={currentPage === 0 || loading}
            className="p-1 rounded hover:bg-gray-100 disabled:opacity-30 transition-colors"
            title="Previous page"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="flex-1 text-center">
            Page {currentPage + 1} / {formatNumber(totalPages)}
          </span>
          <button
            onClick={() => goToPage(currentPage + 1)}
            disabled={currentPage >= totalPages - 1 || loading}
            className="p-1 rounded hover:bg-gray-100 disabled:opacity-30 transition-colors"
            title="Next page"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
          <button
            onClick={() => goToPage(totalPages - 1)}
            disabled={currentPage >= totalPages - 1 || loading}
            className="p-1 rounded hover:bg-gray-100 disabled:opacity-30 transition-colors"
            title="Last page"
          >
            <ChevronsRight className="w-4 h-4" />
          </button>
          <div className="flex items-center gap-1 ml-2 pl-2 border-l border-gray-200">
            <Search className="w-3 h-3 text-gray-400" />
            <input
              type="number"
              min={1}
              placeholder="Line #"
              value={jumpToLine}
              onChange={(e) => setJumpToLine(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleJumpToLine()}
              className="w-16 px-1.5 py-0.5 text-xs border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-blue-400"
            />
            <button
              onClick={handleJumpToLine}
              className="px-1.5 py-0.5 text-[10px] bg-gray-100 rounded hover:bg-gray-200 transition-colors"
            >
              Go
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
