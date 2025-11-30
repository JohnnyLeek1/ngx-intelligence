import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { HelpCircle, Terminal, ExternalLink, Star, AlertCircle } from 'lucide-react';

interface RecommendedModel {
  readonly name: string;
  readonly description: string;
  readonly priority?: number;
}

interface ModelPullHelpDialogProps {
  recommendedModels: readonly RecommendedModel[];
}

export function ModelPullHelpDialog({ recommendedModels }: ModelPullHelpDialogProps) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-5 w-5 text-muted-foreground hover:text-foreground"
        >
          <HelpCircle className="h-4 w-4" />
          <span className="sr-only">Help with pulling Ollama models</span>
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>How to Pull Ollama Models</DialogTitle>
          <DialogDescription>
            A guide for downloading and using AI models locally with Ollama
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {/* What is Ollama */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold">What is Ollama?</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Ollama is a tool that allows you to run large language models (LLMs) locally on your machine.
              Unlike cloud-based AI services, your data stays private and you have full control.
              Before you can use a model, you need to download (or "pull") it first.
            </p>
          </div>

          {/* How to Pull a Model */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <Terminal className="h-4 w-4" />
              How to Pull a Model
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Open your terminal or command prompt and use the following command:
            </p>
            <div className="bg-muted rounded-md p-4 font-mono text-sm">
              <code>ollama pull &lt;model-name&gt;</code>
            </div>
          </div>

          {/* Examples */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold">Recommended Models for Document Processing</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Here are our recommended models. Copy and paste these commands to pull them:
            </p>

            <div className="space-y-3">
              {recommendedModels.slice(0, 3).map((model) => (
                <div key={model.name} className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Badge variant="default" className="text-xs">
                      <Star className="h-3 w-3 mr-1" />
                      Recommended
                    </Badge>
                    <span className="text-sm font-medium">{model.name}</span>
                  </div>
                  <div className="bg-muted rounded-md p-3 font-mono text-sm flex items-center justify-between gap-2">
                    <code>ollama pull {model.name}</code>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 px-2 text-xs"
                      onClick={() => {
                        navigator.clipboard.writeText(`ollama pull ${model.name}`);
                      }}
                    >
                      Copy
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground pl-3">
                    {model.description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Why These Models */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold">Why These Models?</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              These models are specifically chosen for their excellent performance in document processing tasks:
            </p>
            <ul className="text-sm text-muted-foreground space-y-2 list-disc list-inside pl-2">
              <li>Extracting key information from documents</li>
              <li>Identifying correspondents and parties involved</li>
              <li>Generating descriptive titles and summaries</li>
              <li>Automatically tagging and categorizing content</li>
            </ul>
            <p className="text-sm text-muted-foreground leading-relaxed">
              They strike a good balance between speed, accuracy, and resource usage.
            </p>
          </div>

          {/* Additional Resources */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold">Additional Resources</h3>
            <div className="space-y-2">
              <a
                href="https://ollama.com/library"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-sm text-primary hover:underline"
              >
                <ExternalLink className="h-4 w-4" />
                Browse all available models
              </a>
              <a
                href="https://ollama.com/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-sm text-primary hover:underline"
              >
                <ExternalLink className="h-4 w-4" />
                Ollama documentation
              </a>
            </div>
          </div>

          {/* Tip */}
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-sm">
              <span className="font-semibold">Tip:</span> After pulling a model, click the "Refresh Models"
              button above to see it appear in the dropdown list.
            </AlertDescription>
          </Alert>
        </div>
      </DialogContent>
    </Dialog>
  );
}
