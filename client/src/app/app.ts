import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

type ChatMessage = {
  role: 'user';
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

  protected sendMessage(): void {
    const text = this.draft().trim();

    if (!text) {
      return;
    }

    this.messages.update((messages) => [...messages, { role: 'user', text }]);
    this.draft.set('');
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
    this.messages.set([]);
    this.draft.set('');
  }
}
