import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

type ChatMessage = {
  role: 'user' | 'assistant';
  text: string;
};

@Component({
  imports: [FormsModule],
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App {
  protected readonly draft = signal('');
  protected readonly messages = signal<ChatMessage[]>([]);
  protected readonly isSending = signal(false);
  protected readonly serviceError = signal('');

  protected async sendMessage(): Promise<void> {
    const text = this.draft().trim();

    if (!text || this.isSending()) {
      return;
    }

    const conversation = [...this.messages(), { role: 'user' as const, text }];
    this.messages.set(conversation);
    this.draft.set('');
    this.serviceError.set('');
    this.isSending.set(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: conversation.slice(-20).map(({ role, text: content }) => ({ role, content })),
        }),
      });
      const result = await response.json() as { reply?: string; detail?: string };

      if (!response.ok) {
        throw new Error(result.detail ?? 'The AI service could not complete this request.');
      }

      this.messages.update((messages) => [
        ...messages,
        { role: 'assistant', text: result.reply ?? '' },
      ]);
    } catch (error) {
      this.serviceError.set(
        error instanceof TypeError
          ? 'Could not reach the API. Make sure the FastAPI server is running.'
          : error instanceof Error
            ? error.message
            : 'The AI service could not complete this request.',
      );
    } finally {
      this.isSending.set(false);
    }
  }

  protected handleEnter(event: KeyboardEvent): void {
    if (event.key !== 'Enter' || event.shiftKey || event.isComposing) {
      return;
    }

    event.preventDefault();
    this.sendMessage();
  }

  protected usePrompt(prompt: string): void {
    this.draft.set(prompt);
  }

  protected startNewChat(): void {
    if (this.isSending()) {
      return;
    }

    this.messages.set([]);
    this.draft.set('');
    this.serviceError.set('');
  }
}
