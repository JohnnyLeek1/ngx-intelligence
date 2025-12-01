import { useState } from 'react';
import { useDocumentStats, useRecentDocuments, useDailyMetrics } from '@/hooks/useDocuments';
import { useQueueStats, useProcessNow, useResetQueue } from '@/hooks/useQueue';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
import { AlertCustom } from '@/components/ui/alert-custom';
import { FileText, CheckCircle, XCircle, Clock, TrendingUp, TrendingDown, PlayCircle, Gauge, Timer, Minus, RotateCcw } from 'lucide-react';
import { formatProcessingTime, formatRelativeTime } from '@/lib/utils';
import type { ProcessingStatus } from '@/types';

interface TrendData {
  label: string;
  isImprovement: boolean;
  isNeutral?: boolean;
}

function StatCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
  trendData
}: {
  title: string;
  value: string | number;
  description: string;
  icon: any;
  trend?: string;
  trendData?: TrendData;
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
        {trendData && (
          <p className={`text-xs mt-1 flex items-center gap-1 ${
            trendData.isNeutral
              ? 'text-muted-foreground'
              : trendData.isImprovement
                ? 'text-green-600'
                : 'text-red-600'
          }`}>
            {trendData.isNeutral ? (
              <Minus className="h-3 w-3" />
            ) : trendData.isImprovement ? (
              <TrendingUp className="h-3 w-3" />
            ) : (
              <TrendingDown className="h-3 w-3" />
            )}
            {trendData.label}
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

// Helper function to calculate confidence trend
function calculateConfidenceTrend(todayConfidence: number | null, yesterdayConfidence: number | null): TrendData | undefined {
  if (todayConfidence === null || yesterdayConfidence === null) {
    return undefined;
  }

  const change = todayConfidence - yesterdayConfidence;
  const percentChange = Math.abs(change * 100);

  if (Math.abs(change) < 0.01) {
    return {
      label: 'Same as yesterday',
      isImprovement: false,
      isNeutral: true,
    };
  }

  return {
    label: `${change > 0 ? '+' : '-'}${percentChange.toFixed(1)}% vs yesterday`,
    isImprovement: change > 0,
  };
}

// Helper function to calculate processing time trend
function calculateProcessingTimeTrend(todayTimeMs: number | null, yesterdayTimeMs: number | null): TrendData | undefined {
  if (todayTimeMs === null || yesterdayTimeMs === null) {
    return undefined;
  }

  const change = todayTimeMs - yesterdayTimeMs;

  if (Math.abs(change) < 100) {
    return {
      label: 'Same as yesterday',
      isImprovement: false,
      isNeutral: true,
    };
  }

  return {
    label: `${Math.abs(change) >= 1000 ? formatProcessingTime(Math.abs(change)) : `${Math.round(Math.abs(change))}ms`} ${change > 0 ? 'slower' : 'faster'} than yesterday`,
    isImprovement: change < 0, // Lower is better for processing time
  };
}

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useDocumentStats();
  const { data: queueStats, isLoading: queueLoading } = useQueueStats();
  const { data: recentDocs, isLoading: recentLoading } = useRecentDocuments(10);
  const { data: dailyMetrics, isLoading: dailyMetricsLoading } = useDailyMetrics();
  const processNow = useProcessNow();
  const resetQueue = useResetQueue();
  const [processResult, setProcessResult] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);

  const handleProcessNow = async () => {
    setProcessResult(null);
    try {
      const result = await processNow.mutateAsync(10);
      // Determine message type based on content
      const type = result.queued === 0 ? 'info' : 'success';
      setProcessResult({ message: result.message, type });
      setTimeout(() => setProcessResult(null), 5000);
    } catch (error) {
      setProcessResult({ message: 'Failed to queue documents for processing', type: 'error' });
      setTimeout(() => setProcessResult(null), 5000);
    }
  };

  const handleResetQueue = async () => {
    setProcessResult(null);
    try {
      const result = await resetQueue.mutateAsync();
      setProcessResult({ message: result.message, type: 'success' });
      setTimeout(() => setProcessResult(null), 5000);
    } catch (error) {
      setProcessResult({ message: 'Failed to reset queue statistics', type: 'error' });
      setTimeout(() => setProcessResult(null), 5000);
    }
  };

  if (statsLoading || queueLoading || dailyMetricsLoading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-96 mt-2" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
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
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
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
          title="Average Confidence"
          value={dailyMetrics?.today?.avg_confidence_score !== null && dailyMetrics?.today?.avg_confidence_score !== undefined
            ? `${Math.round(dailyMetrics.today.avg_confidence_score * 100)}%`
            : 'N/A'}
          description="Today's average score"
          icon={Gauge}
          trendData={calculateConfidenceTrend(
            dailyMetrics?.today?.avg_confidence_score ?? null,
            dailyMetrics?.yesterday?.avg_confidence_score ?? null
          )}
        />
        <StatCard
          title="Average Processing Time"
          value={dailyMetrics?.today?.avg_processing_time_ms !== null && dailyMetrics?.today?.avg_processing_time_ms !== undefined
            ? formatProcessingTime(dailyMetrics.today.avg_processing_time_ms)
            : 'N/A'}
          description="Today's average time"
          icon={Timer}
          trendData={calculateProcessingTimeTrend(
            dailyMetrics?.today?.avg_processing_time_ms ?? null,
            dailyMetrics?.yesterday?.avg_processing_time_ms ?? null
          )}
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
            <div className="flex items-center gap-2">
              <Button
                onClick={handleResetQueue}
                disabled={resetQueue.isPending}
                variant="outline"
                size="sm"
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                {resetQueue.isPending ? 'Clearing...' : 'Clear Stats'}
              </Button>
              <Button
                onClick={handleProcessNow}
                disabled={processNow.isPending}
                size="sm"
              >
                <PlayCircle className="h-4 w-4 mr-2" />
                {processNow.isPending ? 'Processing...' : 'Process Now'}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {processResult && (
            <AlertCustom
              variant={processResult.type}
              message={processResult.message}
            />
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
                        {doc.suggested_data?.title || `Document #${doc.paperless_document_id}`}
                      </p>
                      <StatusBadge status={doc.status} />
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {formatRelativeTime(doc.processed_at)}
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
