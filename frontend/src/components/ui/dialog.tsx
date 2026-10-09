import * as D from '@radix-ui/react-dialog';
import {X} from 'lucide-react';
import type {ReactNode} from 'react';
export const Dialog=D.Root;
export function DialogContent({title,description,children}:{title:string;description:string;children:ReactNode}) {return <D.Portal><D.Overlay className="dialog-overlay"/><D.Content className="dialog-content"><D.Title className="dialog-title">{title}</D.Title><D.Description className="muted">{description}</D.Description><D.Close className="dialog-close" aria-label="Close dialog"><X size={18}/></D.Close>{children}</D.Content></D.Portal>;}
