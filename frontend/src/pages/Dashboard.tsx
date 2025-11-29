import { useState } from 'react';
import { useDocumentStats, useRecentDocuments } from '@/hooks/useDocuments';
import { useQueueStats, useProcessNow } from '@/hooks/useQueue';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { FileText, CheckCircle, XCircle, Clock, TrendingUp, PlayCircle, AlertCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { formatProcessingTime } from '@/lib/utils';
import type { ProcessingStatus } from '@/types';

function StatCard({
  title,
  value,
  description,
  icon: Icon,
  trend
}: {
  title: string;
  value: string | number;
  description: string;
  icon: any;
  trend?: string;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-muted-foreground">
          {description}
        </p>
        {trend && (
          <p className="text-xs text-green-600 mt-1 flex items-center gap-1">
            <TrendingUp className="h-3 w-3" />
            {trend}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

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

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useDocumentStats();
  const { data: queueStats, isLoading: queueLoading } = useQueueStats();
  const { data: recentDocs, isLoading: recentLoading } = useRecentDocuments(10);
  const processNow = useProcessNow();
  const [processResult, setProcessResult] = useState<string | null>(null);

  const handleProcessNow = async () => {
    setProcessResult(null);
    try {
      const result = await processNow.mutateAsync(10);
      setProcessResult(result.message);
      setTimeout(() => setProcessResult(null), 5000);
    } catch (error) {
      setProcessResult('Failed to queue documents for processing');
      setTimeout(() => setProcessResult(null), 5000);
    }
  };

  if (statsLoading || queueLoading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-96 mt-2" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardHeader className="space-y-0 pb-2">
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16" />
                <Skeleton className="h-3 w-32 mt-2" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Overview of your document processing activity
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Documents"
          value={stats?.total || 0}
          description="All processed documents"
          icon={FileText}
        />
        <StatCard
          title="Success Rate"
          value={`${Math.round(stats?.success_rate || 0)}%`}
          description="Successfully processed"
          icon={CheckCircle}
          trend={stats && stats.success_rate > 90 ? "Excellent performance" : undefined}
        />
        <StatCard
          title="Failed"
          value={stats?.failed || 0}
          description="Processing failures"
          icon={XCircle}
        />
        <StatCard
          title="Queue"
          value={queueStats?.queued || 0}
          description={`${queueStats?.processing || 0} processing now`}
          icon={Clock}
        />
      </div>

      {/* Queue Status */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Processing Queue</CardTitle>
              <CardDescription>Real-time queue status</CardDescription>
            </div>
            <Button
              onClick={handleProcessNow}
              disabled={processNow.isPending}
              size="sm"
            >
              <PlayCircle className="h-4 w-4 mr-2" />
              {processNow.isPending ? 'Processing...' : 'Process Now'}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {processResult && (
            <Alert variant={processResult.includes('Failed') ? 'destructive' : 'default'}>
              {processResult.includes('Failed') ? (
                <AlertCircle className="h-4 w-4" />
              ) : (
                <CheckCircle className="h-4 w-4" />
              )}
              <AlertDescription>{processResult}</AlertDescription>
            </Alert>
          )}
          <div className="grid gap-4 md:grid-cols-4">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Queued</p>
              <p className="text-2xl font-bold">{queueStats?.queued || 0}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Processing</p>
              <p className="text-2xl font-bold">{queueStats?.processing || 0}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Completed</p>
              <p className="text-2xl font-bold text-green-600">{queueStats?.completed || 0}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Failed</p>
              <p className="text-2xl font-bold text-red-600">{queueStats?.failed || 0}</p>
            </div>
          </div>
          {queueStats && queueStats.total > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Overall Progress</span>
                <span className="font-medium">
                  {Math.round(((queueStats.completed || 0) / queueStats.total) * 100)}%
                </span>
              </div>
              <Progress value={((queueStats.completed || 0) / queueStats.total) * 100} />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Last 10 processed documents</CardDescription>
        </CardHeader>
        <CardContent>
          {recentLoading ? (
            <p className="text-muted-foreground text-sm">Loading recent documents...</p>
          ) : !recentDocs || recentDocs.length === 0 ? (
            <p className="text-muted-foreground text-sm">No recent documents</p>
          ) : (
            <div className="space-y-3">
              {recentDocs.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between py-3 border-b last:border-0"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium truncate">
                        Document #{doc.paperless_document_id}
                      </p>
                      <StatusBadge status={doc.status} />
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {formatDistanceToNow(new Date(doc.processed_at), { addSuffix: true })}
                      {doc.confidence_score && (
                        <> • Confidence: {Math.round(doc.confidence_score * 100)}%</>
                      )}
                    </p>
                  </div>
                  {doc.processing_time_ms && (
                    <div className="text-xs text-muted-foreground">
                      {formatProcessingTime(doc.processing_time_ms)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Alerts Section */}
      {stats && stats.failed > 0 && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Alerts</CardTitle>
            <CardDescription>Issues requiring attention</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-start gap-3">
              <XCircle className="h-5 w-5 text-destructive mt-0.5" />
              <div>
                <p className="text-sm font-medium">Failed Processing Jobs</p>
                <p className="text-sm text-muted-foreground">
                  {stats.failed} document{stats.failed !== 1 ? 's' : ''} failed to process.
                  Check the History page for details.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
