import { useState } from 'react';
import { useDocuments } from '@/hooks/useDocuments';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Search, RefreshCw, Eye } from 'lucide-react';
import { format } from 'date-fns';
import { formatProcessingTime } from '@/lib/utils';
import type { ProcessingStatus, DocumentFilterRequest, ProcessedDocument } from '@/types';

function StatusBadge({ status }: { status: ProcessingStatus }) {
  const variants: Record<ProcessingStatus, { variant: any; label: string }> = {
    success: { variant: 'success' as any, label: 'Success' },
    failed: { variant: 'destructive', label: 'Failed' },
    pending_approval: { variant: 'warning' as any, label: 'Pending' },
    queued: { variant: 'secondary', label: 'Queued' },
    processing: { variant: 'default', label: 'Processing' },
  };

  const config = variants[status] || variants.success;
  return <Badge variant={config.variant}>{config.label}</Badge>;
}

export default function HistoryPage() {
  const [filters, setFilters] = useState<DocumentFilterRequest>({
    limit: 50,
    offset: 0,
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDoc, setSelectedDoc] = useState<ProcessedDocument | null>(null);

  const { data, isLoading, refetch } = useDocuments(filters);

  const handleRefresh = () => {
    refetch();
  };

  const handleStatusFilter = (status: ProcessingStatus | undefined) => {
    setFilters(prev => ({ ...prev, status, offset: 0 }));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Processing History</h1>
          <p className="text-muted-foreground mt-1">
            View and manage document processing history
          </p>
        </div>
        <Button onClick={handleRefresh} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
          <CardDescription>Filter documents by status or search</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by document ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
            <div className="flex gap-2 flex-wrap">
              <Button
                variant={filters.status === undefined ? 'default' : 'outline'}
                size="sm"
                onClick={() => handleStatusFilter(undefined)}
              >
                All
              </Button>
              <Button
                variant={filters.status === 'success' ? 'default' : 'outline'}
                size="sm"
                onClick={() => handleStatusFilter('success')}
              >
                Success
              </Button>
              <Button
                variant={filters.status === 'failed' ? 'default' : 'outline'}
                size="sm"
                onClick={() => handleStatusFilter('failed')}
              >
                Failed
              </Button>
              <Button
                variant={filters.status === 'pending_approval' ? 'default' : 'outline'}
                size="sm"
                onClick={() => handleStatusFilter('pending_approval')}
              >
                Pending
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Documents Table */}
      <Card>
        <CardHeader>
          <CardTitle>Documents</CardTitle>
          <CardDescription>
            {data ? `Showing ${data.documents.length} of ${data.total} documents` : 'Loading...'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : !data || data.documents.length === 0 ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-muted-foreground">No documents found</p>
            </div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Document ID</TableHead>
                    <TableHead>Processed Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Confidence</TableHead>
                    <TableHead>Processing Time</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.documents.map((doc) => (
                    <TableRow key={doc.id}>
                      <TableCell className="font-medium">
                        #{doc.paperless_document_id}
                      </TableCell>
                      <TableCell>
                        {format(new Date(doc.processed_at), 'MMM dd, yyyy HH:mm')}
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={doc.status} />
                      </TableCell>
                      <TableCell>
                        {doc.confidence_score !== null && doc.confidence_score !== undefined
                          ? `${Math.round(doc.confidence_score * 100)}%`
                          : '-'}
                      </TableCell>
                      <TableCell>
                        {formatProcessingTime(doc.processing_time_ms)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setSelectedDoc(doc)}
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}

          {/* Pagination */}
          {data && data.total > filters.limit! && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-muted-foreground">
                Showing {filters.offset! + 1} to {Math.min(filters.offset! + filters.limit!, data.total)} of {data.total}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setFilters(prev => ({ ...prev, offset: Math.max(0, prev.offset! - prev.limit!) }))}
                  disabled={filters.offset === 0}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setFilters(prev => ({ ...prev, offset: prev.offset! + prev.limit! }))}
                  disabled={filters.offset! + filters.limit! >= data.total}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Document Details Dialog */}
      <Dialog open={!!selectedDoc} onOpenChange={(open) => !open && setSelectedDoc(null)}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Document Details</DialogTitle>
            <DialogDescription>
              Document #{selectedDoc?.paperless_document_id}
            </DialogDescription>
          </DialogHeader>
          {selectedDoc && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Status</p>
                  <div className="mt-1">
                    <StatusBadge status={selectedDoc.status} />
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Processed Date</p>
                  <p className="mt-1">{format(new Date(selectedDoc.processed_at), 'MMM dd, yyyy HH:mm:ss')}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Confidence Score</p>
                  <p className="mt-1">
                    {selectedDoc.confidence_score !== null && selectedDoc.confidence_score !== undefined
                      ? `${Math.round(selectedDoc.confidence_score * 100)}%`
                      : 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Processing Time</p>
                  <p className="mt-1">{formatProcessingTime(selectedDoc.processing_time_ms)}</p>
                </div>
              </div>

              {selectedDoc.suggested_data && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">Suggested Data</p>
                  <pre className="bg-muted p-3 rounded-md text-xs overflow-x-auto">
                    {JSON.stringify(selectedDoc.suggested_data, null, 2)}
                  </pre>
                </div>
              )}

              {selectedDoc.error_message && (
                <div>
                  <p className="text-sm font-medium text-destructive mb-2">Error Message</p>
                  <p className="bg-destructive/10 p-3 rounded-md text-sm text-destructive">
                    {selectedDoc.error_message}
                  </p>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
