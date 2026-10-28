import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

type AnalysisRequest = {
  product_name: string;
  category: string;
  target_audience: string;
  description: string;
  tone: string;
};

type AnalysisResult = {
  score: number;
  summary: string;
  strengths: string[];
  improvements: string[];
  optimized_description: string;
};

@Component({
  imports: [FormsModule],
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App {
  private readonly http = inject(HttpClient);

  protected readonly productName = signal('');
  protected readonly category = signal('');
  protected readonly audience = signal('');
  protected readonly description = signal('');
  protected readonly tone = signal('Persuasive');
  protected readonly result = signal<AnalysisResult | null>(null);
  protected readonly isAnalyzing = signal(false);
  protected readonly errorMessage = signal('');

  protected async analyze(): Promise<void> {
    if (this.isAnalyzing()) {
      return;
    }

    const request: AnalysisRequest = {
      product_name: this.productName().trim(),
      category: this.category().trim(),
      target_audience: this.audience().trim(),
      description: this.description().trim(),
      tone: this.tone(),
    };

    if (!request.product_name || !request.description) {
      this.errorMessage.set('Add a product name and description to get started.');
      return;
    }

    this.isAnalyzing.set(true);
    this.errorMessage.set('');
    this.result.set(null);

    try {
      const result = await firstValueFrom(
        this.http.post<AnalysisResult>('/api/analyze', request),
      );
      this.result.set(result);
    } catch (error: unknown) {
      this.errorMessage.set(this.getErrorMessage(error));
    } finally {
      this.isAnalyzing.set(false);
    }
  }

  protected get descriptionLength(): number {
    return this.description().length;
  }

  private getErrorMessage(error: unknown): string {
    if (error instanceof HttpErrorResponse && error.status === 0) {
      return 'Could not reach the analyzer API. Start the backend and try again.';
    }

    if (error instanceof HttpErrorResponse && error.status === 404) {
      return 'The analyzer API endpoint is not available yet. Configure POST /api/analyze in the backend.';
    }

    if (error instanceof HttpErrorResponse) {
      return error.error?.detail ?? 'The analyzer could not complete this request.';
    }

    return 'An unexpected error occurred while analyzing this description.';
  }
}
