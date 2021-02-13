<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace App\Controller;

use App\Entity\Comment;
use App\Entity\Post;
use App\Event\CommentCreatedEvent;
use App\Form\CommentType;
use App\Repository\PostRepository;
use App\Repository\TagRepository;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\Cache;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\IsGranted;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\ParamConverter;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\EventDispatcher\EventDispatcherInterface;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;

/**
 * Controller managing API.
 *
 * @Route("/api")
 *
 * @author Ryan Weaver <weaverryan@gmail.com>
 * @author Javier Eguiluz <javier.eguiluz@gmail.com>
 */
class ApiController extends AbstractController
{
    /**
     * @Route("/posts", defaults={"_format"="json"}, methods="GET", name="api_index")
     */
    public function index(Request $request, PostRepository $posts, TagRepository $tags): Response
    {
        $tag = null;

        if ($request->query->has('tag')) {
            /** @var \App\Entity\Tag $tag */
            $tag = $tags->findOneBy(['name' => $request->query->get('tag')]);
        }

        $latestPosts = $posts->findLatest($request->query->get('page', 1), $tag);

        $results = [];
        foreach ($latestPosts->getResults() as $post) {
            $results[] = $this->postToJson($post);
        }

        return $this->json($results);
    }

    /**
     * @Route("/tags", defaults={"page": "1", "_format"="json"}, methods="GET", name="api_tags")
     */
    public function tags(TagRepository $tags): Response
    {
        /** @var \App\Entity\Tag[] $tags */
        $tags = $tags->findAll();

        $results = [];
        foreach ($tags as $tag) {
            $results[] = [
                'name' => $tag->getName(),
            ];
        }

        return $this->json($results);
    }

    /**
     * @Route("/search", defaults={"_format": "json"}, methods="GET", name="api_search")
     */
    public function search(Request $request, PostRepository $posts): Response
    {
        $query = $request->query->get('q', '');
        $limit = $request->query->get('l', 10);

        $foundPosts = $posts->findBySearchQuery($query, $limit);

        $results = [];
        foreach ($foundPosts as $post) {
            $results[] = $this->postToJson($post);
        }

        return $this->json($results);
    }

    private function postToJson(Post $post): array
    {
        return [
            'title'   => htmlspecialchars($post->getTitle(), ENT_COMPAT | ENT_HTML5),
            'date'    => $post->getPublishedAt()->format('M d, Y'),
            'author'  => htmlspecialchars($post->getAuthor()->getFullName(), ENT_COMPAT | ENT_HTML5),
            'summary' => htmlspecialchars($post->getSummary(), ENT_COMPAT | ENT_HTML5),
            'url'     => $this->generateUrl('blog_post', ['slug' => $post->getSlug()]),
        ];
    }
}
