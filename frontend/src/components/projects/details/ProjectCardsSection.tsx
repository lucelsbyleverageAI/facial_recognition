'use client';

import React from 'react';
import { useReactTable, getCoreRowModel, flexRender, getPaginationRowModel, getSortedRowModel, getFilteredRowModel, SortingState, ColumnFiltersState } from '@tanstack/react-table';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, ArrowUpDown, RefreshCw, Copy, Check } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { format } from 'date-fns';
import Link from 'next/link';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useQuery } from '@apollo/client';
import { GET_CARDS_BY_PROJECT } from '@/lib/graphql/queries';
import { Card as ProjectCard } from '@/types';
import { Skeleton } from '@/components/ui/skeleton';
import { AddNewCardModal } from './AddNewCardModal';
import { formatStatus } from '@/lib/utils';

interface ProjectCardsSectionProps {
  projectId: string;
}

// Helper function for copy to clipboard
const useCopyToClipboard = () => {
  const [copiedId, setCopiedId] = React.useState<string | null>(null);
  
  const copyToClipboard = (id: string) => {
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };
  
  return { copiedId, copyToClipboard };
};

// Column definitions for the table
const getColumns = (copyId: string | null, onCopy: (id: string) => void, projectId: string) => [
  {
    accessorKey: 'card_id',
    header: 'Card ID',
    cell: ({ row }: { row: any }) => {
      const id = row.original.card_id;
      return (
        <div className="flex items-center gap-1">
          <span className="font-mono text-xs">{id.substring(0, 6)}</span>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon" className="h-4 w-4" onClick={() => onCopy(id)}>
                  {copyId === id ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p className="text-xs">{copyId === id ? 'Copied!' : 'Copy full ID'}</p>
                {!copyId && <p className="text-xs font-mono mt-1 text-muted-foreground">{id}</p>}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      );
    },
  },
  {
    accessorKey: 'card_name',
    header: ({ column }: { column: any }) => (
      <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>
        Card Name <ArrowUpDown className="ml-2 h-4 w-4" />
      </Button>
    ),
    cell: ({ row }: { row: any }) => <div className="font-medium">{row.original.card_name}</div>,
  },
  {
    accessorKey: 'status',
    header: ({ column }: { column: any }) => (
      <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>
        Status <ArrowUpDown className="ml-2 h-4 w-4" />
      </Button>
    ),
    cell: ({ row }: { row: any }) => {
      const status = row.original.status;
      let variant: "default" | "secondary" | "outline" | "destructive" = 'secondary';
      
      switch (status) {
        case 'complete': variant = 'default'; break;
        case 'processing': variant = 'secondary'; break; 
        case 'generating_embeddings': variant = 'secondary'; break;
        case 'paused': variant = 'outline'; break;
        case 'error': variant = 'destructive'; break;
        case 'pending': variant = 'secondary'; break;
      }
      
      return <Badge variant={variant}>{formatStatus(status)}</Badge>;
    },
  },
  {
    accessorKey: 'created_at',
    header: ({ column }: { column: any }) => (
      <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>
        Created <ArrowUpDown className="ml-2 h-4 w-4" />
      </Button>
    ),
    cell: ({ row }: { row: any }) => <div>{format(new Date(row.original.created_at), 'MMM d, yyyy p')}</div>,
  },
  {
    id: 'actions',
    cell: ({ row }: { row: any }) => {
      const card = row.original;
      return (
        <Link href={`/projects/${projectId}/${card.card_id}`}>
          <Button variant="outline" size="sm">Select</Button>
        </Link>
      );
    },
  },
];

// Adapt useCards hook to fetch all cards for client-side handling
const useProjectCards = (projectId: string) => {
  const { data, loading, error, refetch } = useQuery(GET_CARDS_BY_PROJECT, {
    variables: { projectId, limit: 1000, offset: 0 }, // Fetch up to 1000 cards
    skip: !projectId,
  });

  return {
    cards: (data?.cards as ProjectCard[]) || [],
    totalCount: data?.cards_aggregate?.aggregate?.count || 0,
    loading,
    error,
    refetch,
  };
};

export function ProjectCardsSection({ projectId }: ProjectCardsSectionProps) {
  const { cards, loading, error, refetch } = useProjectCards(projectId);
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([]);
  const { copiedId, copyToClipboard } = useCopyToClipboard();
  
  const columns = React.useMemo(() => getColumns(copiedId, copyToClipboard, projectId), [copiedId, projectId]);

  const table = useReactTable({
    data: cards,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    state: {
      sorting,
      columnFilters,
    },
    initialState: {
      pagination: {
        pageSize: 10, // Default page size
      },
    },
  });
  
  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-32" /> {/* Title */} 
          <div className="flex gap-2">
             <Skeleton className="h-9 w-32" /> {/* Add button */} 
             <Skeleton className="h-9 w-9 rounded-full" /> {/* Refresh button */} 
          </div>
        </div>
        <Skeleton className="h-10 w-1/3" /> {/* Search input */} 
        <Skeleton className="h-[400px] w-full" /> {/* Table */} 
        <div className="flex justify-between items-center">
          <Skeleton className="h-8 w-24" /> {/* Page info */} 
          <div className="flex gap-2">
            <Skeleton className="h-8 w-16" />
            <Skeleton className="h-8 w-16" />
            <Skeleton className="h-8 w-16" />
            <Skeleton className="h-8 w-16" />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return <div className="text-destructive">Error loading cards: {error.message}</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <h2 className="text-2xl font-semibold">Cards</h2>
        <div className="flex items-center gap-2">
          <AddNewCardModal projectId={projectId} />
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" size="icon" onClick={() => refetch()} disabled={loading}>
                  <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Refresh Cards</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>

      <Input
        placeholder="Filter by card name..."
        value={(table.getColumn('card_name')?.getFilterValue() as string) ?? ''}
        onChange={(event) =>
          table.getColumn('card_name')?.setFilterValue(event.target.value)
        }
        className="max-w-sm"
      />

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id} data-state={row.getIsSelected() && 'selected'}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  No cards found for this project.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination Controls */}
      <div className="flex items-center justify-between space-x-2 py-4">
        <div className="text-sm text-muted-foreground">
          Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
          {' '} | {table.getFilteredRowModel().rows.length} card(s)
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => table.setPageIndex(0)}
            disabled={!table.getCanPreviousPage()}
          >
            <ChevronsLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            onClick={() => table.setPageIndex(table.getPageCount() - 1)}
            disabled={!table.getCanNextPage()}
          >
            <ChevronsRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}