'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText, RefreshCw, AlertCircle, Loader2, ServerOff } from 'lucide-react';
import { useFrameResults } from "@/hooks/useFrameResults";
import { ResultsFilters } from "./ResultsFilters";
import { ResultsTable } from "./ResultsTable";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ApolloError } from '@apollo/client';

interface ResultsTabProps {
  projectId: string;
  cardId: string;
}

export default function ResultsTab({ projectId, cardId }: ResultsTabProps) {
  const [refreshKey, setRefreshKey] = React.useState(0);

  const {
    frames,
    clips,
    loading,
    error,
    pagination,
    filters
  } = useFrameResults({
    projectId,
    cardId,
    limit: 10,
    page: 0,
    refreshKey
  });

  const [previousLoading, setPreviousLoading] = useState(loading);
  const scrollYRef = useRef<number | null>(null);

  const handlePageChangeWrapper = (newPage: number) => {
    scrollYRef.current = window.scrollY;
    pagination.handlePageChange(newPage);
  };

  const handleRowsPerPageChangeWrapper = (newRowsPerPage: number) => {
    scrollYRef.current = window.scrollY;
    pagination.handleRowsPerPageChange(newRowsPerPage);
  };

  const handleFiltersChangeWrapper = (newFilters: Partial<typeof filters.current>) => {
    scrollYRef.current = window.scrollY;
    filters.handleFiltersChange(newFilters);
  };

  const handleRefresh = () => {
    scrollYRef.current = window.scrollY;
    setRefreshKey(prev => prev + 1);
  };

  useEffect(() => {
    if (previousLoading && !loading && scrollYRef.current !== null) {
      window.scrollTo({ top: scrollYRef.current, behavior: 'instant' });
      scrollYRef.current = null;
    }
    setPreviousLoading(loading);
  }, [loading, previousLoading]);

  React.useEffect(() => {
    if (error) {
      console.error("Detailed error object:", error);
    }
  }, [error]);

  if (error) {
    let errorMessage = "An error occurred while loading frame results.";
    
    if (typeof error.message === 'string') {
      errorMessage = error.message;
    } 
    else if (error.networkError) { 
      errorMessage = error.networkError.message;
    } 
    else if (error.graphQLErrors && error.graphQLErrors.length > 0) {
      errorMessage = error.graphQLErrors.map(e => e.message).join("; ");
    } 
    else {
      errorMessage = "An unknown error occurred. Check console for details.";
    }
    
    const isConnectionError = (typeof errorMessage === 'string' && (
      errorMessage.includes('Failed to fetch') || 
      errorMessage.includes('Network error') ||
      errorMessage.includes('socket') ||
      errorMessage.includes('connection')
    )) || errorMessage.includes("Failed to fetch");
    
    return (
      <div className="space-y-6">
        <div className="flex justify-end space-x-2">
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry Connection
          </Button>
        </div>
        
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error Loading Results</AlertTitle>
          <AlertDescription>
            {errorMessage}
          </AlertDescription>
        </Alert>
        
        <div className="bg-muted/40 rounded-lg p-8">
          <div className="flex items-center gap-3 mb-4">
            <ServerOff className="h-6 w-6 text-destructive" />
            <h3 className="text-lg font-medium">Connection Issue Detected</h3>
          </div>
          <p className="text-muted-foreground mb-4">
            {isConnectionError 
              ? "There appears to be a connection issue with the database or backend server." 
              : "There was a problem loading the frame results data."}
          </p>
          <div className="bg-card p-4 rounded-md mb-4">
            <h4 className="font-medium mb-2">Troubleshooting Steps:</h4>
            <ol className="list-decimal list-inside space-y-2 text-muted-foreground">
              <li>Verify that your Hasura GraphQL server is running</li>
              <li>Check that your environment variables are correctly set in <code className="bg-muted px-1 py-0.5 rounded text-xs">.env.local</code>:
                <ul className="list-disc list-inside ml-6 mt-1 text-xs font-mono">
                  <li>NEXT_PUBLIC_HASURA_GRAPHQL_URL</li>
                  <li>NEXT_PUBLIC_HASURA_GRAPHQL_WS_URL</li>
                  <li>NEXT_PUBLIC_HASURA_ADMIN_SECRET</li>
                </ul>
              </li>
              <li>Make sure there is network connectivity between your frontend and backend</li>
              <li>Check the browser console for more detailed error messages</li>
            </ol>
          </div>
          <p className="text-sm text-muted-foreground">
            After addressing these issues, click "Retry Connection" above to attempt to load the data again.
          </p>
        </div>
      </div>
    );
  }

  if (loading && !frames.length) {
    return (
      <div className="flex flex-col items-center justify-center py-12 space-y-4">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-lg font-medium">Loading frame results...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-end space-x-2">
        <Button variant="outline" size="sm">
          <FileText className="mr-2 h-4 w-4" />
          Generate Report
        </Button>
        <Button variant="outline" size="sm" onClick={handleRefresh}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>
      
      <h2 className="text-2xl font-bold tracking-tight">Results</h2>
      
      <p className="text-muted-foreground">
        View and filter frame results for this card. Results update in real-time as frames are processed.
      </p>
      
      <ResultsFilters
        clips={clips}
        onFilterChange={handleFiltersChangeWrapper}
        currentFilters={filters.current}
      />
      
      <ResultsTable 
        frames={frames}
        pagination={{
          ...pagination,
          handlePageChange: handlePageChangeWrapper,
          handleRowsPerPageChange: handleRowsPerPageChangeWrapper,
        }}
        loading={loading}
      />
      
      {!loading && frames.length === 0 && (
        <div className="bg-muted/40 rounded-lg p-8 text-center">
          <p className="text-lg font-medium mb-2">No frames available</p>
          <p className="text-muted-foreground">
            There are no frames to display. This could be because:
          </p>
          <ul className="text-muted-foreground list-disc list-inside my-4 mx-auto max-w-md text-left">
            <li>No frames have been processed for this card yet</li>
            <li>The frames don't match your current filter criteria</li>
            <li>There might be an issue with the connection to the database</li>
          </ul>
        </div>
      )}
    </div>
  );
} 