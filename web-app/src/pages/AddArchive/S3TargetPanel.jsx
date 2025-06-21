import { Container, Header, FormField, Input } from '@cloudscape-design/components';
import { useState } from 'react';

export default function S3TargetPanel({ targetState, setTargetState }) {
    const [values, setValues] = useState({ bucket: '', folder: '' });

    const onChange = (attribute, value) => {
        const newState = { ...values, [attribute]: value };
        setValues(newState);
        setTargetState(current => {
            const safe = current ?? { body: {} };
            const body = { ...safe.body, [attribute]: value };
            return { ...safe, body };
        });
    };

    return (
        <Container header={<Header variant="h2">Target (S3)</Header>}>
            <FormField label="S3 Bucket" stretch={true}>
                <Input
                    value={values.bucket}
                    onChange={({ detail }) => onChange('bucket', detail.value)}
                    placeholder="my-archive-bucket"
                />
            </FormField>
            <FormField label="Folder Name" stretch={true}>
                <Input
                    value={values.folder}
                    onChange={({ detail }) => onChange('folder', detail.value)}
                    placeholder="application-name"
                />
            </FormField>
        </Container>
    );
}
