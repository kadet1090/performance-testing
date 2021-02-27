<?php

namespace App\CommonMark;

use League\CommonMark\Block\Element\AbstractBlock;
use League\CommonMark\Block\Element\FencedCode;
use League\CommonMark\Block\Element\IndentedCode;
use League\CommonMark\Block\Renderer\BlockRendererInterface;
use League\CommonMark\ConfigurableEnvironmentInterface;
use League\CommonMark\ElementRendererInterface;
use League\CommonMark\Extension\ExtensionInterface;
use League\CommonMark\Extension\Table\Table;
use League\CommonMark\Extension\Table\TableRenderer;
use Symfony\Contracts\Service\ServiceProviderInterface;
use Symfony\Contracts\Service\ServiceSubscriberInterface;

class KeylighterExtension implements ExtensionInterface, ServiceSubscriberInterface
{
    private $provider;

    public function __construct(ServiceProviderInterface $provider)
    {
        $this->provider = $provider;
    }

    public function register(ConfigurableEnvironmentInterface $environment)
    {
        $environment->addBlockRenderer(FencedCode::class, $this->provider->get(KeylighterCodeRenderer::class), 150);
        $environment->addBlockRenderer(IndentedCode::class, $this->provider->get(KeylighterCodeRenderer::class), 150);

        $environment->addBlockRenderer(Table::class, new class implements BlockRendererInterface {
            private $decorated;

            public function __construct()
            {
                $this->decorated = new TableRenderer();
            }

            public function render(AbstractBlock $block, ElementRendererInterface $htmlRenderer, bool $inTightList = false)
            {
                $element = $this->decorated->render($block, $htmlRenderer, $inTightList);
                $element->setAttribute('class', 'table');

                return $element;
            }
        });
    }

    /**
     * @inheritDoc
     */
    public static function getSubscribedServices()
    {
        return [
            KeylighterCodeRenderer::class
        ];
    }
}
