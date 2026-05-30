import { logger } from './logger.js';

export class CircuitBreaker {
  private failureCount = 0;
  private lastFailureTime = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';
  
  private threshold = 5;
  private timeout = 60000; // 1 minute

  async execute<T>(fn: () => Promise<T>, context?: string): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailureTime > this.timeout) {
        this.state = 'half-open';
      } else {
        throw new Error(`Circuit breaker is open (${context})`);
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure(context, error);
      throw error;
    }
  }

  private onSuccess() {
    this.failureCount = 0;
    this.state = 'closed';
  }

  private onFailure(context: string | undefined, error: any) {
    this.failureCount++;
    this.lastFailureTime = Date.now();

    logger.error(`Circuit breaker failure (${this.failureCount}/${this.threshold})`, {
      context,
      error: (error as Error).message
    });

    if (this.failureCount >= this.threshold) {
      this.state = 'open';
      logger.error(`⚠️ Circuit breaker opened: ${context}`);
    }
  }

  getState() {
    return {
      state: this.state,
      failureCount: this.failureCount,
      lastFailureTime: this.lastFailureTime
    };
  }
}

export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  initialDelay: number = 1000,
  context?: string
): Promise<T> {
  let lastError: any;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      const delay = initialDelay * Math.pow(2, attempt);
      
      logger.warn(`Attempt ${attempt + 1}/${maxRetries} failed (${context}), retrying in ${delay}ms`, {
        error: (error as Error).message
      });
      
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  throw lastError;
}
