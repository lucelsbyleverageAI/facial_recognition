'use client';

import { useState } from 'react';
import { useMutation } from '@apollo/client';
import { ADD_NEW_CARD, GET_CARDS_BY_PROJECT } from '@/lib/graphql/queries';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { PlusCircle, Loader2 } from 'lucide-react';
import React from 'react';

interface AddNewCardModalProps {
  projectId: string;
}

export function AddNewCardModal({ projectId }: AddNewCardModalProps) {
  const [open, setOpen] = useState(false);
  const [cardName, setCardName] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);
  
  const [addCard, { loading }] = useMutation(ADD_NEW_CARD, {
    // Refetch the cards list after mutation to update the table
    refetchQueries: [
      { query: GET_CARDS_BY_PROJECT, variables: { projectId, limit: 1000, offset: 0 } } 
    ],
    onError: (err) => {
      console.error("Error adding new card:", err);
      setError(err.message);
    },
    onCompleted: () => {
      // Reset form and close modal on success
      setCardName('');
      setDescription('');
      setError(null);
      setOpen(false);
    }
  });

  const handleSubmit = () => {
    if (!cardName.trim()) {
      setError('Card Name is required.');
      return;
    }
    setError(null);
    addCard({
      variables: {
        projectId,
        cardName: cardName.trim(),
        description: description.trim() || null, // Send null if empty
      }
    });
  };

  // Reset state when modal is closed
  const handleOpenChange = (isOpen: boolean) => {
    setOpen(isOpen);
    if (!isOpen) {
      setCardName('');
      setDescription('');
      setError(null);
    }
  }

  // Type the event parameter
  const handleDescriptionChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setDescription(e.target.value);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button>
          <PlusCircle className="mr-2 h-4 w-4" /> Add New Card
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Add New Card</DialogTitle>
          <DialogDescription>
            Enter the details for the new card.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <label htmlFor="name" className="text-right">
              Card Name
            </label>
            <Input 
              id="name" 
              value={cardName} 
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCardName(e.target.value)}
              className="col-span-3" 
              disabled={loading}
            />
          </div>
          <div className="grid grid-cols-4 items-start gap-4">
            <label htmlFor="description" className="text-right pt-2">
              Description
            </label>
            <Textarea
              id="description"
              value={description}
              onChange={handleDescriptionChange}
              className="col-span-3"
              rows={3}
              placeholder="(Optional)"
              disabled={loading}
            />
          </div>
          {error && (
            <p className="text-sm text-destructive col-span-4 text-center">{error}</p>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={loading}>
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />} 
            Add Card
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
} 