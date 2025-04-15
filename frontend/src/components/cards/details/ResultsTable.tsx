import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { ExpandableImage } from "@/components/ui/expandable-image";
import { Badge } from "@/components/ui/badge";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Frame, DetectedFace } from "@/types";

interface ResultsTableProps {
  frames: Frame[];
  pagination: {
    currentPage: number;
    rowsPerPage: number;
    totalCount: number;
    handlePageChange: (page: number) => void;
    handleRowsPerPageChange: (rowsPerPage: number) => void;
  };
  loading: boolean;
}

export function ResultsTable({ frames, pagination, loading }: ResultsTableProps) {
  const {
    currentPage,
    rowsPerPage,
    totalCount,
    handlePageChange,
    handleRowsPerPageChange
  } = pagination;

  // Total pages calculation
  const totalPages = Math.ceil(totalCount / rowsPerPage);

  // Function to shorten ID for display
  const shortenId = (id: string) => {
    return id.substring(0, 8);
  };

  // Function to render status badge with appropriate color
  const renderStatusBadge = (status: string) => {
    let variant: "default" | "destructive" | "outline" | "secondary" | null | undefined = "outline";
    
    switch (status) {
      case "queued":
        variant = "secondary";
        break;
      case "detecting_faces":
      case "detection_complete":
        variant = "default";
        break;
      case "recognition_complete":
        variant = "default";
        break;
      case "error":
        variant = "destructive";
        break;
    }

    return (
      <Badge variant={variant}>
        {status.replace(/_/g, " ")}
      </Badge>
    );
  };

  return (
    <div className="space-y-4">
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="sticky top-0 z-10 w-[100px] bg-card">ID</TableHead>
              <TableHead className="sticky top-0 z-10 w-[120px] bg-card">Status</TableHead>
              <TableHead className="sticky top-0 z-10 bg-card">Clip</TableHead>
              <TableHead className="sticky top-0 z-10 bg-card">Timestamp</TableHead>
              <TableHead className="sticky top-0 z-10 w-[120px] bg-card">Frame</TableHead>
              <TableHead className="sticky top-0 z-10 w-[200px] bg-card">Matched Faces</TableHead>
              <TableHead className="sticky top-0 z-10 text-right bg-card">Detected</TableHead>
              <TableHead className="sticky top-0 z-10 text-right bg-card">Matched</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading && frames.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="h-24 text-center">
                  Loading frame data...
                </TableCell>
              </TableRow>
            ) : !loading && frames.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="h-24 text-center">
                  No frames found with the current filters.
                </TableCell>
              </TableRow>
            ) : (
              frames.map((frame) => {
                // Calculate detection and match counts
                const detectedCount = frame.detected_faces_aggregate.aggregate.count;
                const matchedCount = frame.detected_faces.reduce(
                  (count: number, face: DetectedFace) => 
                    (face.face_matches && face.face_matches.length > 0) 
                      ? count + 1 
                      : count, 
                  0
                );

                return (
                  <TableRow key={frame.frame_id}>
                    <TableCell className="font-mono text-xs">
                      {shortenId(frame.frame_id)}
                    </TableCell>
                    <TableCell>{renderStatusBadge(frame.status)}</TableCell>
                    <TableCell>{frame.clip.filename}</TableCell>
                    <TableCell>{frame.timestamp}</TableCell>
                    <TableCell>
                      {(frame.processed_frame_image_path || frame.raw_frame_image_path) && (
                        <ExpandableImage 
                          src={frame.processed_frame_image_path || frame.raw_frame_image_path}
                          alt={`Frame ${shortenId(frame.frame_id)}`}
                          width={100}
                          height={60}
                          className="object-cover"
                        />
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex min-h-[40px] gap-1 overflow-x-auto pb-2 max-w-[180px]">
                        {frame.detected_faces.flatMap((face: DetectedFace) => 
                          face.face_matches.map((match) => (
                            <ExpandableImage
                              key={match.match_id}
                              src={match.consent_face.face_image_path}
                              alt={match.consent_face.consent_profile.person_name || 'Unknown person'}
                              width={40}
                              height={40}
                              className="rounded-full object-cover border-2 border-green-500 flex-shrink-0"
                            />
                          ))
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <Badge variant="outline" className="font-mono">
                        {detectedCount}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Badge
                        variant={matchedCount > 0 ? "default" : "outline"}
                        className={`font-mono ${ 
                          detectedCount > 0 && matchedCount === 0
                            ? "bg-amber-500" 
                            : matchedCount > 0 
                            ? "bg-green-500"
                            : ""
                        }`}
                      >
                        {matchedCount}
                      </Badge>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-between pt-4">
        <div className="text-sm text-muted-foreground">
          Showing {frames.length > 0 ? currentPage * rowsPerPage + 1 : 0} to{" "}
          {Math.min((currentPage + 1) * rowsPerPage, totalCount)} of {totalCount} entries
        </div>
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            <p className="text-sm font-medium">Rows per page</p>
            <select
              className="h-8 rounded-md border border-input bg-background px-2"
              value={rowsPerPage}
              onChange={(e) => handleRowsPerPageChange(Number(e.target.value))}
            >
              {[5, 10, 20, 50].map((pageSize) => (
                <option key={pageSize} value={pageSize}>
                  {pageSize}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="icon"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 0}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <div className="text-sm font-medium">
              Page {currentPage + 1} of {totalPages || 1}
            </div>
            <Button
              variant="outline"
              size="icon"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages - 1 || totalPages === 0}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
} 